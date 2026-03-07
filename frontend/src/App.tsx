import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ConsultationPage from './pages/ConsultationPage';
import ResultsPage from './pages/ResultsPage';
import PatientPortalPage from './pages/PatientPortalPage';
import type { ProcessingResult, Consultation } from './types';

type UserMode = 'none' | 'doctor' | 'patient';

function App() {
  const [userMode, setUserMode] = useState<UserMode>('none');
  const [doctor, setDoctor] = useState<{ id: string; name: string; speciality: string; hospital: string } | null>(null);
  const [currentResult, setCurrentResult] = useState<ProcessingResult | null>(null);
  const [currentConsultation, setCurrentConsultation] = useState<Consultation | null>(null);
  const [patientPhone, setPatientPhone] = useState('');

  const handleDoctorLogin = (doc: { id: string; name: string; speciality: string; hospital: string }) => {
    setDoctor(doc);
    setUserMode('doctor');
  };

  const handlePatientLogin = (phone: string) => {
    setPatientPhone(phone);
    setUserMode('patient');
  };

  const handleLogout = () => {
    setDoctor(null);
    setUserMode('none');
    setCurrentResult(null);
    setCurrentConsultation(null);
    setPatientPhone('');
  };

  if (userMode === 'none') {
    return <LoginPage onLogin={handleDoctorLogin} onPatientLogin={handlePatientLogin} />;
  }

  if (userMode === 'patient') {
    return <PatientPortalPage onLogout={handleLogout} phone={patientPhone} />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <DashboardPage
              doctor={doctor!}
              onLogout={handleLogout}
              onSelectConsultation={(c) => setCurrentConsultation(c)}
            />
          }
        />
        <Route
          path="/consultation"
          element={
            <ConsultationPage
              doctor={doctor!}
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
                doctor={doctor!}
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
