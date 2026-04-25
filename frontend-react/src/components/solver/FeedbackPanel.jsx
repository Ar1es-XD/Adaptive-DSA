import React from 'react';

export default function FeedbackPanel({
  feedback = {},
  attempts = 0,
  maxAttempts = 3,
  showSolution = false,
  solution = null,
  nextProblem = null,
  onNextProblem = () => {}
}) {
  if (!feedback || Object.keys(feedback).length === 0) {
    return null;
  }

  const isCorrect = feedback.correct;
  const maxAttemptsReached = attempts >= maxAttempts;

  return (
    <div>
      {/* Correct Answer */}
      {isCorrect && (
        <div className="mb-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-4">
            <h3 className="text-2xl font-bold text-green-700 mb-2">🎉 Correct!</h3>
            <p className="text-green-600 mb-4">Excellent work! You've solved this problem.</p>
            
            {feedback.mastery !== undefined && (
              <div className="bg-white p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Your mastery on this topic:</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-green-500 h-3 rounded-full transition-all"
                      style={{ width: `${Math.min(feedback.mastery, 100)}%` }}
                    ></div>
                  </div>
                  <span className="font-bold text-gray-900">
                    {Math.round(feedback.mastery || 0)}%
                  </span>
                </div>
              </div>
            )}
          </div>

          {nextProblem && (
            <button
              onClick={onNextProblem}
              className="w-full px-4 py-3 bg-blue-500 text-white font-bold rounded-lg hover:bg-blue-600 transition"
            >
              Next Problem →
            </button>
          )}
        </div>
      )}

      {/* Incorrect Answer */}
      {!isCorrect && !maxAttemptsReached && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-4">
          <h3 className="text-lg font-bold text-yellow-700 mb-2">❌ Not Quite</h3>
          <p className="text-yellow-600 mb-4">
            Attempt {attempts} of {maxAttempts}. Keep trying!
          </p>
          
          {feedback.hint && (
            <div className="bg-white p-4 rounded-lg border border-yellow-100">
              <p className="text-sm font-bold text-gray-900 mb-1">💡 Hint:</p>
              <p className="text-sm text-gray-700">{feedback.hint}</p>
            </div>
          )}
        </div>
      )}

      {/* Max Attempts Reached - Show Solution */}
      {maxAttemptsReached && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-4">
          <h3 className="text-lg font-bold text-red-700 mb-3">Max Attempts Reached</h3>
          
          {showSolution && solution && (
            <div className="bg-white p-4 rounded-lg border border-red-100 mb-4">
              <p className="text-sm font-bold text-gray-900 mb-2">Solution:</p>
              <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto text-gray-700">
                {solution}
              </pre>
            </div>
          )}

          {nextProblem && (
            <button
              onClick={onNextProblem}
              className="w-full px-4 py-2 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 transition"
            >
              Continue to Next Problem
            </button>
          )}
        </div>
      )}

      {/* Error Message */}
      {feedback.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 font-medium">{feedback.error}</p>
        </div>
      )}
    </div>
  );
}
