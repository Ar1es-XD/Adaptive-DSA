import React, { useState, useEffect } from 'react';

const PROBLEMS = [
  { id: "diag_1", title: "Two Sum", instructions: "Find two numbers adding up to target." },
  { id: "diag_2", title: "Reverse String", instructions: "Reverse the array of characters in-place." },
  { id: "diag_3", title: "Binary Tree Level Order Traversal", instructions: "Return the level order traversal of a binary tree's nodes' values." },
  { id: "diag_4", title: "Longest Substring Without Repeating", instructions: "Find the length of the longest substring without repeating characters." },
  { id: "diag_5", title: "Median of Two Sorted Arrays", instructions: "Find the median of two sorted arrays of size m and n." },
];

export default function DiagnosticTest({ userId, onComplete }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [code, setCode] = useState('');
  const [timeLeft, setTimeLeft] = useState(180);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (timeLeft <= 0 && !submitting) {
      handleSubmit();
      return;
    }
    const timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [timeLeft, submitting]);

  const handleSubmit = async () => {
    setSubmitting(true);
    const problem = PROBLEMS[currentIndex];
    try {
      await fetch('http://127.0.0.1:8000/api/diagnostic/submit-attempt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          problem_id: problem.id,
          submitted_code: code,
          time_spent_seconds: 180 - timeLeft,
        }),
      });

      if (currentIndex < PROBLEMS.length - 1) {
        setCurrentIndex(prev => prev + 1);
        setCode('');
        setTimeLeft(300); // Standard reset for next
        setSubmitting(false);
      } else {
        // Finalize
        const finalizeResponse = await fetch('http://127.0.0.1:8000/api/diagnostic/finalize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            all_problem_ids: PROBLEMS.map(p => p.id),
          }),
        });
        const data = await finalizeResponse.json();
        onComplete({ completed: true }, data.abilityMap);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to submit attempt: " + err.message);
      setSubmitting(false);
    }
  };

  const problem = PROBLEMS[currentIndex];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Problem {currentIndex + 1} of {PROBLEMS.length}</h2>
        <div className={`font-mono text-lg ${timeLeft < 60 ? 'text-red-400' : 'text-slate-300'}`}>
          Time Left: {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
        </div>
      </div>
      
      <div className="mb-4">
        <h3 className="text-xl font-semibold">{problem.title}</h3>
        <p className="text-slate-400 mt-1">{problem.instructions}</p>
      </div>

      <textarea
        className="w-full h-64 p-4 font-mono bg-slate-900 border border-slate-700 rounded text-slate-100"
        value={code}
        onChange={e => setCode(e.target.value)}
        placeholder="Write your solution here..."
      />

      <button 
        disabled={submitting} 
        onClick={handleSubmit} 
        className="mt-4 p-3 bg-green-600 hover:bg-green-500 rounded font-semibold w-full transition-colors"
      >
        {submitting ? "Submitting..." : "Submit Solution"}
      </button>
    </div>
  );
}
