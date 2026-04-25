import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import ProblemSolver from './pages/ProblemSolver';

function App() {
  return (
    <Router>
      <Routes>
        {/* Onboarding: Signup → Waiver → Diagnostic → Plan */}
        <Route path="/" element={<Onboarding />} />
        
        {/* Dashboard: Main learning hub */}
        <Route path="/dashboard" element={<Dashboard />} />
        
        {/* Problem Solver: Solve individual problems */}
        <Route path="/problem/:problemId" element={<ProblemSolver />} />
        
        {/* Catch-all: Redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
