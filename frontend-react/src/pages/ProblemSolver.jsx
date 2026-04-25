import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ProblemDescription from '../components/solver/ProblemDescription';
import CodeEditor from '../components/solver/CodeEditor';
import TestCaseDisplay from '../components/solver/TestCaseDisplay';
import FeedbackPanel from '../components/solver/FeedbackPanel';

const MAX_ATTEMPTS = 3;

export default function ProblemSolver() {
  const { problemId } = useParams();
  const navigate = useNavigate();

  // State
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [testResults, setTestResults] = useState(null);
  const [attemptsUsed, setAttemptsUsed] = useState(0);
  const [showSolution, setShowSolution] = useState(false);
  const [solution, setSolution] = useState(null);
  const [nextProblem, setNextProblem] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load problem on mount
  useEffect(() => {
    if (!problemId) {
      navigate('/dashboard');
      return;
    }

    fetch(`http://localhost:8000/practice/problem?problem_id=${problemId}`)
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          setFeedback({ error: data.error });
          setLoading(false);
          return;
        }
        setProblem(data.problem);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load problem:', err);
        setFeedback({ error: 'Could not load problem. Try again.' });
        setLoading(false);
      });
  }, [problemId, navigate]);

  const handleSubmit = async () => {
    if (!code.trim()) {
      setFeedback({ error: 'Please write some code before submitting' });
      return;
    }

    setSubmitting(true);
    setFeedback(null);

    try {
      const response = await fetch('http://localhost:8000/practice/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem_id: problemId,
          answer: code
        })
      });

      const data = await response.json();

      if (data.error) {
        setFeedback({ error: data.error });
        setSubmitting(false);
        return;
      }

      // Update state from response
      setFeedback(data.feedback || {});
      setTestResults(data.test_results);
      setAttemptsUsed(data.control?.attempts_on_problem || 0);

      if (data.control?.show_solution && data.solution) {
        setShowSolution(true);
        setSolution(data.solution);
      }

      if (data.next_problem) {
        setNextProblem(data.next_problem);
      }
    } catch (err) {
      console.error('Submit error:', err);
      setFeedback({ error: 'Failed to submit: ' + err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextProblem = () => {
    if (nextProblem?.problem_id) {
      navigate(`/problem/${nextProblem.problem_id}`);
    } else {
      navigate('/dashboard');
    }
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading problem...</p>
        </div>
      </div>
    );
  }

  if (!problem) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <p className="text-red-600 mb-4">Problem not found</p>
          <button
            onClick={handleBackToDashboard}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <button
            onClick={handleBackToDashboard}
            className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{problem.title}</h1>
          <div className="w-32"></div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel: Problem Description */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-y-auto max-h-[calc(100vh-150px)]">
          <ProblemDescription problem={problem} />
        </div>

        {/* Right Panel: Editor & Results */}
        <div className="flex flex-col gap-6">
          {/* Code Editor */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <CodeEditor
              code={code}
              onChange={setCode}
              submitting={submitting}
              onSubmit={handleSubmit}
            />
          </div>

          {/* Test Results */}
          {testResults && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <TestCaseDisplay testResults={testResults} />
            </div>
          )}

          {/* Feedback Panel */}
          {feedback && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <FeedbackPanel
                feedback={feedback}
                attempts={attemptsUsed}
                maxAttempts={MAX_ATTEMPTS}
                showSolution={showSolution}
                solution={solution}
                nextProblem={nextProblem}
                onNextProblem={handleNextProblem}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
