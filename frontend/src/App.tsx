import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ConsultationPage from './pages/ConsultationPage';
import ResultsPage from './pages/ResultsPage';
import type { ProcessingResult, Consultation } from './types';

function App() {
  const [doctor, setDoctor] = useState<{ id: string; name: string; speciality: string; hospital: string } | null>(null);
  const [currentResult, setCurrentResult] = useState<ProcessingResult | null>(null);
  const [currentConsultation, setCurrentConsultation] = useState<Consultation | null>(null);

  if (!doctor) {
    return <LoginPage onLogin={setDoctor} />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <DashboardPage
              doctor={doctor}
              onLogout={() => setDoctor(null)}
              onSelectConsultation={(c) => setCurrentConsultation(c)}
            />
          }
        />
        <Route
          path="/consultation"
          element={
            <ConsultationPage
              doctor={doctor}
              consultation={currentConsultation}
              onResult={(result, consultation) => {
                setCurrentResult(result);
                setCurrentConsultation(consultation);
              }}
            />
          }
        />
        <Route
          path="/results"
          element={
            currentResult ? (
              <ResultsPage
                result={currentResult}
                consultation={currentConsultation!}
                doctor={doctor}
              />
            ) : (
              <Navigate to="/" />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
