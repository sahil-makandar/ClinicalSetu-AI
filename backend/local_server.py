"""
Local development server for ClinicalSetu.
Runs the Lambda handler locally with a simple HTTP server.
Requires: pip install boto3
AWS credentials must be configured (aws configure or env vars).
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Add lambda directory to path
sys.path.insert(0, str(Path(__file__).parent / "lambda"))
from process_consultation import lambda_handler


class CORSHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/process":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            print(f"\n{'='*60}")
            print(f"Processing consultation...")

            event = {"body": body}
            result = lambda_handler(event, None)

            self.send_response(result["statusCode"])
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(result["body"].encode("utf-8"))

            parsed = json.loads(result["body"])
            if "metadata" in parsed:
                print(f"Done in {parsed['metadata']['total_processing_time_ms']}ms")
            print(f"{'='*60}\n")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "ClinicalSetu API"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[API] {args[0]}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3001))
    server = HTTPServer(("0.0.0.0", port), CORSHandler)
    print(f"\nClinicalSetu Local API Server")
    print(f"{'='*40}")
    print(f"Running on http://localhost:{port}")
    print(f"Health: http://localhost:{port}/health")
    print(f"API:    POST http://localhost:{port}/api/process")
    print(f"Region: {os.environ.get('AWS_REGION', 'us-east-1')}")
    print(f"{'='*40}\n")
    print("Ensure AWS credentials are configured (aws configure)")
    print("Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()
