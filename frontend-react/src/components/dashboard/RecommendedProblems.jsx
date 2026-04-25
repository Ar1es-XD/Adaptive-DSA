import React from 'react';

const DIFFICULTY_STARS = {
  1: '⭐',
  2: '⭐⭐',
  3: '⭐⭐⭐',
  4: '⭐⭐⭐⭐',
  5: '⭐⭐⭐⭐⭐'
};

const DIFFICULTY_LABEL = {
  1: 'Very Easy',
  2: 'Easy',
  3: 'Medium',
  4: 'Hard',
  5: 'Very Hard'
};

export default function RecommendedProblems({ recommendations = [], onStartProblem }) {
  return (
    <div className="space-y-4">
      {recommendations.slice(0, 3).map((rec, idx) => (
        <div
          key={rec.problem.problem_id}
          className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
                  {rec.topic}
                </span>
                <span className="text-sm text-gray-500">
                  {DIFFICULTY_LABEL[rec.problem.difficulty] || 'Medium'}
                </span>
              </div>
              <h3 className="text-lg font-bold text-gray-900">
                {rec.problem.title}
              </h3>
              <p className="text-gray-500 text-sm mt-2">
                Difficulty: {DIFFICULTY_STARS[rec.problem.difficulty] || '⭐⭐⭐'}
              </p>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Your Mastery</span>
              <span className="text-sm font-bold text-blue-600">
                {Math.round(rec.skill_mastery || 0)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${Math.round(rec.skill_mastery || 0)}%` }}
              ></div>
            </div>
          </div>

          <button
            onClick={() => onStartProblem(rec.problem.problem_id)}
            className="w-full px-4 py-2 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 transition"
          >
            Start Problem
          </button>
        </div>
      ))}
    </div>
  );
}
