import React, { useState } from 'react';
import SignupForm from '../components/onboarding/SignupForm';
import WaiverForm from '../components/onboarding/WaiverForm';
import DiagnosticTest from '../components/onboarding/DiagnosticTest';
import PlanDisplay from '../components/onboarding/PlanDisplay';

export default function OnboardingFlow() {
  const [step, setStep] = useState(1); // 1-4
  const [userData, setUserData] = useState({
    userProfile: null,
    testResult: null,
    abilityMap: null,
    learningPlan: null,
  });

  const handleSignupComplete = (profile, userId) => {
    setUserData(prev => ({ ...prev, userProfile: { ...profile, user_id: userId } }));
    setStep(2);
  };

  const handleWaiverComplete = () => {
    setStep(3);
  };

  const handleTestComplete = (testResult, abilityMap) => {
    setUserData(prev => ({
      ...prev,
      testResult,
      abilityMap,
    }));
    // Generate plan
    fetch('http://127.0.0.1:8000/api/learning-plan/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userData.userProfile.user_id }),
    })
      .then(r => r.json())
      .then(data => {
        setUserData(prev => ({ ...prev, learningPlan: data.learningPlan }));
        setStep(4);
      });
  };

  return (
    <div className="flex justify-center items-center h-screen bg-slate-900 text-slate-100">
      <div className="w-full max-w-4xl p-6 bg-slate-800 rounded-lg shadow-xl">
        {step === 1 && <SignupForm onComplete={handleSignupComplete} />}
        {step === 2 && <WaiverForm onComplete={handleWaiverComplete} />}
        {step === 3 && <DiagnosticTest userId={userData.userProfile?.user_id} onComplete={handleTestComplete} />}
        {step === 4 && <PlanDisplay plan={userData.learningPlan} />}
      </div>
    </div>
  );
}
