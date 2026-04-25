import React, { useState } from 'react';

export default function WaiverForm({ onComplete }) {
  const [checks, setChecks] = useState({
    terms: false,
    privacy: false,
    academic: false,
  });

  const allChecked = checks.terms && checks.privacy && checks.academic;

  return (
    <div>
      <h2 className="text-2xl mb-4 font-bold">Step 2: Agreements & Waiver</h2>
      <div className="h-48 overflow-y-auto p-4 bg-slate-700 rounded text-sm text-slate-300 mb-6">
        <p className="mb-2"><strong>Terms of Use:</strong> By using the Adaptive DSA Tutor, you agree to follow the community guidelines and standard usage allocations.</p>
        <p className="mb-2"><strong>Data Privacy:</strong> Your performance data is used to tailor your learning curve anonymously across the LLM metrics engine.</p>
        <p><strong>Academic Integrity:</strong> You certify that the solutions provided during diagnostics are your own initial efforts.</p>
      </div>

      <div className="flex flex-col gap-3">
        <label className="flex items-center gap-2 cursor-pointer text-slate-300">
          <input type="checkbox" checked={checks.terms} onChange={e => setChecks({ ...checks, terms: e.target.checked })} />
          I agree to the Terms of Use
        </label>
        <label className="flex items-center gap-2 cursor-pointer text-slate-300">
          <input type="checkbox" checked={checks.privacy} onChange={e => setChecks({ ...checks, privacy: e.target.checked })} />
          I understand the Data Privacy Usage
        </label>
        <label className="flex items-center gap-2 cursor-pointer text-slate-300">
          <input type="checkbox" checked={checks.academic} onChange={e => setChecks({ ...checks, academic: e.target.checked })} />
          I certify my own work for the diagnostics
        </label>
      </div>

      <button 
        disabled={!allChecked} 
        onClick={onComplete} 
        className="mt-6 p-3 w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:bg-slate-600 rounded font-semibold transition-colors"
      >
        Save & Continue
      </button>
    </div>
  );
}
