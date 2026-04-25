import React from 'react';

export default function WeakTopics({ weakTopics = [] }) {
  if (!weakTopics || weakTopics.length === 0) {
    return null;
  }

  return (
    <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
      <div className="flex items-start gap-4">
        <span className="text-3xl">🎯</span>
        <div className="flex-1">
          <h3 className="font-bold text-gray-900 mb-2">Areas to Focus On</h3>
          <p className="text-sm text-gray-700 mb-3">
            You're showing weaker performance in these topics. Consider spending extra time here:
          </p>
          <div className="flex flex-wrap gap-2">
            {weakTopics.map((topic) => (
              <span
                key={topic}
                className="inline-block px-3 py-1 bg-orange-100 text-orange-800 text-sm font-medium rounded-full capitalize"
              >
                {topic.replace(/-/g, ' ')}
              </span>
            ))}
          </div>
          <p className="text-sm text-gray-600 mt-4">
            💡 Tip: Spend 30 minutes daily on these topics to improve faster
          </p>
        </div>
      </div>
    </div>
  );
}
