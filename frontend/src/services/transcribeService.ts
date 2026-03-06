import {
  TranscribeStreamingClient,
  StartMedicalStreamTranscriptionCommand,
  type MedicalTranscriptResultStream,
} from '@aws-sdk/client-transcribe-streaming';
import { fromCognitoIdentityPool } from '@aws-sdk/credential-providers';

const REGION = import.meta.env.VITE_AWS_REGION || 'us-east-1';
const IDENTITY_POOL_ID = import.meta.env.VITE_COGNITO_IDENTITY_POOL_ID || '';

const SAMPLE_RATE = 16000;
const LANGUAGE_CODE = 'en-US'; // Transcribe Medical supports en-US and en-AU

type TranscriptCallback = (text: string, isFinal: boolean) => void;

let client: TranscribeStreamingClient | null = null;

function getClient(): TranscribeStreamingClient {
  if (!client) {
    client = new TranscribeStreamingClient({
      region: REGION,
      credentials: fromCognitoIdentityPool({
        clientConfig: { region: REGION },
        identityPoolId: IDENTITY_POOL_ID,
      }),
    });
  }
  return client;
}

async function getAudioStream(stream: MediaStream): Promise<AsyncIterable<{ AudioEvent: { AudioChunk: Uint8Array } }>> {
  const audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, 1, 1);

  source.connect(processor);
  processor.connect(audioContext.destination);

  const audioChunks: Uint8Array[] = [];
  let resolveChunk: (() => void) | null = null;
  let stopped = false;

  processor.onaudioprocess = (event) => {
    if (stopped) return;
    const input = event.inputBuffer.getChannelData(0);
    // Convert Float32 PCM to Int16 PCM
    const pcm16 = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    audioChunks.push(new Uint8Array(pcm16.buffer));
    if (resolveChunk) {
      resolveChunk();
      resolveChunk = null;
    }
  };

  const asyncIterator: AsyncIterable<{ AudioEvent: { AudioChunk: Uint8Array } }> = {
    [Symbol.asyncIterator]() {
      return {
        async next() {
          if (stopped && audioChunks.length === 0) {
            processor.disconnect();
            source.disconnect();
            audioContext.close();
            return { done: true, value: undefined };
          }
          while (audioChunks.length === 0) {
            await new Promise<void>((resolve) => {
              resolveChunk = resolve;
            });
            if (stopped && audioChunks.length === 0) {
              processor.disconnect();
              source.disconnect();
              audioContext.close();
              return { done: true, value: undefined };
            }
          }
          const chunk = audioChunks.shift()!;
          return {
            done: false,
            value: { AudioEvent: { AudioChunk: chunk } },
          };
        },
      };
    },
  };

  // Expose a stop method via a property on the iterable
  (asyncIterator as any).stop = () => {
    stopped = true;
    if (resolveChunk) {
      resolveChunk();
      resolveChunk = null;
    }
  };

  return asyncIterator;
}

export interface TranscribeSession {
  stop: () => void;
  stream: MediaStream;
}

export async function startTranscription(
  onTranscript: TranscriptCallback,
  onError: (error: string) => void,
): Promise<TranscribeSession> {
  if (!IDENTITY_POOL_ID) {
    throw new Error('Cognito Identity Pool ID not configured. Set VITE_COGNITO_IDENTITY_POOL_ID.');
  }

  const mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      sampleRate: SAMPLE_RATE,
      echoCancellation: true,
      noiseSuppression: true,
    },
  });

  const audioStream = await getAudioStream(mediaStream);

  const command = new StartMedicalStreamTranscriptionCommand({
    LanguageCode: LANGUAGE_CODE,
    MediaEncoding: 'pcm',
    MediaSampleRateHertz: SAMPLE_RATE,
    AudioStream: audioStream,
    Specialty: 'PRIMARYCARE',
    Type: 'CONVERSATION',
    EnableChannelIdentification: false,
  });

  const transcribeClient = getClient();

  // Start streaming in background
  transcribeClient.send(command).then(async (response) => {
    if (!response.TranscriptResultStream) return;

    try {
      for await (const event of response.TranscriptResultStream as AsyncIterable<MedicalTranscriptResultStream>) {
        if ('TranscriptEvent' in event && event.TranscriptEvent?.Transcript?.Results) {
          for (const result of event.TranscriptEvent.Transcript.Results) {
            if (result.Alternatives && result.Alternatives.length > 0) {
              const transcript = result.Alternatives[0].Transcript || '';
              const isFinal = !result.IsPartial;
              onTranscript(transcript, isFinal);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        onError(err.message || 'Transcription stream error');
      }
    }
  }).catch((err: any) => {
    onError(err.message || 'Failed to start transcription');
  });

  return {
    stop: () => {
      (audioStream as any).stop?.();
      mediaStream.getTracks().forEach((t) => t.stop());
    },
    stream: mediaStream,
  };
}

export function isTranscribeConfigured(): boolean {
  return !!IDENTITY_POOL_ID;
}
