import React from 'react';

export default function AnalyticsPanel({
  total_attempts = 0,
  correct_count = 0,
  overall_success_rate = 0,
  distinct_problems_attempted = 0
}) {
  const cards = [
    {
      label: 'Total Attempts',
      value: total_attempts,
      color: 'bg-blue-50 text-blue-600',
      icon: '📝'
    },
    {
      label: 'Success Rate',
      value: `${Math.round(overall_success_rate * 100)}%`,
      color: 'bg-green-50 text-green-600',
      icon: '✅'
    },
    {
      label: 'Problems Solved',
      value: distinct_problems_attempted,
      color: 'bg-purple-50 text-purple-600',
      icon: '🎯'
    },
    {
      label: 'Correct Answers',
      value: correct_count,
      color: 'bg-amber-50 text-amber-600',
      icon: '⭐'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.label} className={`${card.color} p-6 rounded-lg border border-gray-200 shadow-sm`}>
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-2">{card.label}</p>
              <p className="text-3xl font-bold">{card.value}</p>
            </div>
            <span className="text-2xl">{card.icon}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
