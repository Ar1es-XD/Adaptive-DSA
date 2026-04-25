import React from 'react';

export default function ProblemDescription({ problem }) {
  if (!problem) return null;

  const DIFFICULTY_LABEL = {
    1: 'Very Easy',
    2: 'Easy',
    3: 'Medium',
    4: 'Hard',
    5: 'Very Hard'
  };

  return (
    <div className="p-8">
      {/* Title & Meta */}
      <h2 className="text-3xl font-bold text-gray-900 mb-4">{problem.title}</h2>
      
      <div className="flex flex-wrap gap-3 mb-6">
        <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full capitalize">
          {problem.topic}
        </span>
        <span className={`inline-block px-3 py-1 text-xs font-semibold rounded-full ${
          problem.difficulty <= 2
            ? 'bg-green-100 text-green-700'
            : problem.difficulty <= 3
            ? 'bg-yellow-100 text-yellow-700'
            : 'bg-red-100 text-red-700'
        }`}>
          {DIFFICULTY_LABEL[problem.difficulty] || 'Medium'}
        </span>
      </div>

      {/* Description */}
      <div className="mb-8">
        <h3 className="font-bold text-gray-900 mb-2">Description</h3>
        <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
          {problem.description}
        </p>
      </div>

      {/* Examples */}
      {problem.examples && problem.examples.length > 0 && (
        <div className="mb-8">
          <h3 className="font-bold text-gray-900 mb-3">Examples</h3>
          <div className="space-y-3">
            {problem.examples.map((ex, idx) => (
              <div key={idx} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <p className="text-sm font-mono text-gray-700 mb-2">
                  <span className="font-bold">Input:</span> {ex.input}
                </p>
                <p className="text-sm font-mono text-gray-700">
                  <span className="font-bold">Output:</span> {ex.output}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Constraints */}
      {problem.constraints && problem.constraints.length > 0 && (
        <div className="mb-8">
          <h3 className="font-bold text-gray-900 mb-2">Constraints</h3>
          <ul className="text-gray-700 space-y-1">
            {problem.constraints.map((constraint, idx) => (
              <li key={idx} className="text-sm">• {constraint}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
