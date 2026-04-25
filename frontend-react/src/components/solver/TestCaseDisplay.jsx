import React from 'react';

export default function TestCaseDisplay({ testResults = [] }) {
  if (!testResults || testResults.length === 0) {
    return null;
  }

  return (
    <div>
      <h3 className="font-bold text-gray-900 mb-4">Test Results</h3>
      <div className="space-y-3">
        {testResults.map((result, idx) => {
          const passed = result.passed;
          return (
            <div
              key={idx}
              className={`p-4 rounded-lg border-2 ${
                passed
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-lg font-bold ${passed ? 'text-green-600' : 'text-red-600'}`}>
                  {passed ? '✓' : '✗'}
                </span>
                <span className={`font-bold ${passed ? 'text-green-600' : 'text-red-600'}`}>
                  Test {idx + 1}: {passed ? 'PASS' : 'FAIL'}
                </span>
              </div>
              
              <div className="text-sm text-gray-700 space-y-1">
                <p><span className="font-medium">Input:</span> {result.input}</p>
                <p><span className="font-medium">Expected:</span> {result.expected}</p>
                <p><span className="font-medium">Got:</span> {result.actual}</p>
                {result.error && (
                  <p className="text-red-600"><span className="font-medium">Error:</span> {result.error}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
