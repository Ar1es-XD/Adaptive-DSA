import React from 'react';

const MASTERY_COLOR = (percent) => {
  if (percent >= 80) return 'bg-green-500';
  if (percent >= 60) return 'bg-yellow-500';
  if (percent >= 40) return 'bg-orange-500';
  return 'bg-red-500';
};

const MASTERY_BG = (percent) => {
  if (percent >= 80) return 'bg-green-50 border-green-200';
  if (percent >= 60) return 'bg-yellow-50 border-yellow-200';
  if (percent >= 40) return 'bg-orange-50 border-orange-200';
  return 'bg-red-50 border-red-200';
};

export default function ProgressCard({
  topic = 'Unknown',
  masteryPercent = 0
}) {
  return (
    <div className={`${MASTERY_BG(masteryPercent)} p-4 rounded-lg border`}>
      <h4 className="font-bold text-gray-900 capitalize mb-3">{topic}</h4>
      
      <div className="mb-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-600">Mastery</span>
          <span className="text-sm font-bold text-gray-900">{masteryPercent}%</span>
        </div>
        <div className="w-full bg-gray-300 rounded-full h-2">
          <div
            className={`${MASTERY_COLOR(masteryPercent)} h-2 rounded-full transition-all`}
            style={{ width: `${masteryPercent}%` }}
          ></div>
        </div>
      </div>

      <div className="text-xs text-gray-500">
        {masteryPercent < 50 && '⚠️ Needs practice'}
        {masteryPercent >= 50 && masteryPercent < 80 && '📈 Making progress'}
        {masteryPercent >= 80 && '🎉 Well mastered'}
      </div>
    </div>
  );
}
