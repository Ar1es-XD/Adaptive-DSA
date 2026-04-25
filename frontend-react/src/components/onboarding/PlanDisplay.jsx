import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function PlanDisplay({ plan, userData }) {
  const navigate = useNavigate();
  if (!plan) return <div>Loading your plan...</div>;

  const getAbilityLabel = (level) => {
    const labels = ["", "Foundational", "Emerging", "Developing", "Proficient", "Advanced"];
    return labels[level] || "Unknown";
  };

  const startLearning = () => {
    // Save user_id to localStorage so Dashboard can find it
    if (userData?.userProfile?.user_id) {
      localStorage.setItem('user_id', userData.userProfile.user_id);
    }
    // Navigate to dashboard
    navigate('/dashboard');
  };

  return (
    <div>
      <h2 className="text-3xl font-bold mb-2">Your Personalized Roadmap</h2>
      <p className="text-slate-400 mb-6 font-medium text-lg">
        We assessed your problem solving ability as <span className="text-emerald-400 font-bold">{getAbilityLabel(plan.ability_level)}</span>.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-slate-700 p-4 rounded border-t-4 border-emerald-500">
          <h3 className="font-bold mb-2">Phase 1 (Fundamentals)</h3>
          <ul className="list-disc list-inside text-slate-300">
            {plan.phase_1_concepts.map(c => <li key={c}>{c.replace('_', ' ')}</li>)}
          </ul>
        </div>
        <div className="bg-slate-700 p-4 rounded border-t-4 border-blue-500">
          <h3 className="font-bold mb-2">Phase 2 (Core Patterns)</h3>
          <ul className="list-disc list-inside text-slate-300">
            {plan.phase_2_concepts.map(c => <li key={c}>{c.replace('_', ' ')}</li>)}
          </ul>
        </div>
        <div className="bg-slate-700 p-4 rounded border-t-4 border-purple-500">
          <h3 className="font-bold mb-2">Phase 3 (Optimization)</h3>
          <ul className="list-disc list-inside text-slate-300">
            {plan.phase_3_concepts.map(c => <li key={c}>{c.replace('_', ' ')}</li>)}
          </ul>
        </div>
      </div>

      <div className="bg-slate-900 p-4 rounded mb-6 text-sm">
        <div className="mb-2"><strong>Focus Areas:</strong> {plan.focus_areas.join(', ').replace("-", " ")}</div>
        <div className="mb-2"><strong>Pace:</strong> {plan.daily_problem_count} problems/day</div>
        <div><strong>Timeline:</strong> {plan.estimated_weeks} weeks total</div>
      </div>

      <button onClick={startLearning} className="w-full text-xl p-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-transform transform hover:scale-105 shadow-lg">
        Start Learning
      </button>
    </div>
  );
}
