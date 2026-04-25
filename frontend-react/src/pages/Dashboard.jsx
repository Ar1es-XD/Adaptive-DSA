import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AnalyticsPanel from '../components/dashboard/AnalyticsPanel';
import RecommendedProblems from '../components/dashboard/RecommendedProblems';
import WeakTopics from '../components/dashboard/WeakTopics';
import ProgressCard from '../components/dashboard/ProgressCard';

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [topicProgress, setTopicProgress] = useState({});

  useEffect(() => {
    // Check authentication
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      navigate('/');
      return;
    }

    // Fetch all dashboard data in parallel
    Promise.all([
      fetch('http://localhost:8000/api/analytics/summary').then(r => r.json()),
      fetch('http://localhost:8000/api/recommend').then(r => r.json()),
    ])
      .then(([analyticsData, recsData]) => {
        setAnalytics(analyticsData);
        setRecommendations(recsData);
        
        // Build topic progress from recommendations
        const topics = {};
        recsData.forEach(rec => {
          if (rec.skill_mastery !== undefined) {
            topics[rec.topic] = rec.skill_mastery;
          }
        });
        setTopicProgress(topics);
        setLoading(false);
      })
      .catch(err => {
        console.error('Dashboard load error:', err);
        setError('Failed to load dashboard. Please refresh.');
        setLoading(false);
      });
  }, [navigate]);

  const handleStartProblem = (problemId) => {
    sessionStorage.setItem('current_problem_id', problemId);
    navigate(`/problem/${problemId}`);
  };

  const handleLogout = () => {
    localStorage.removeItem('user_id');
    sessionStorage.clear();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-600">
          <p className="text-lg font-semibold mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Welcome Back! 👋</h1>
            <p className="text-sm text-gray-500 mt-1">Keep up the momentum with your learning</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium hover:bg-gray-100 rounded-lg transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Analytics Section */}
        {analytics && (
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Your Progress</h2>
            <AnalyticsPanel {...analytics} />
          </section>
        )}

        {/* Recommended Problems Section */}
        {recommendations.length > 0 && (
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Recommended for You</h2>
            <RecommendedProblems
              recommendations={recommendations}
              onStartProblem={handleStartProblem}
            />
          </section>
        )}

        {/* Topic Progress Section */}
        {Object.keys(topicProgress).length > 0 && (
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Topic Mastery</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(topicProgress).map(([topic, mastery]) => (
                <ProgressCard
                  key={topic}
                  topic={topic}
                  masteryPercent={Math.round(mastery || 0)}
                />
              ))}
            </div>
          </section>
        )}

        {/* Weak Topics Section */}
        {analytics?.weak_topics && analytics.weak_topics.length > 0 && (
          <section>
            <WeakTopics weakTopics={analytics.weak_topics} />
          </section>
        )}
      </main>
    </div>
  );
}
