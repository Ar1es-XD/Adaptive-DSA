import { useEffect, useState } from "react";

export default function App() {
  const [problem, setProblem] = useState(null);
  const [lastProblem, setLastProblem] = useState(null);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [view, setView] = useState("practice");
  const [reviewData, setReviewData] = useState([]);
  const [recommendData, setRecommendData] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [solution, setSolution] = useState(null);
  const [stats, setStats] = useState({ attempts: 0, correct: 0 });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.querySelector("textarea")?.focus();
  }, [problem]);

  const safeFetch = async (url, options) => {
    try {
      setError(null);
      const res = await fetch(url, options);
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const startSession = async () => {
    setLoading(true);
    try {
      const data = await safeFetch("http://127.0.0.1:8000/practice/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: "arrays" }),
      });

      setProblem(data.problem || null);
      setLastProblem(data.problem || null);
      setFeedback(null);
      setSolution(null);
      setAnswer("");
      setStats({ attempts: 0, correct: 0 });
      setView("practice");
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!problem || !answer.trim()) return;

    setLoading(true);

    try {
      const data = await safeFetch("http://127.0.0.1:8000/practice/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          problem_id: problem.problem_id,
          answer,
        }),
      });

      setFeedback(data.feedback || null);
      setSolution(data.control?.show_solution ? data.solution : null);
      setAnswer("");
      setStats((s) => ({
        attempts: s.attempts + 1,
        correct: s.correct + (data.feedback?.correct ? 1 : 0),
      }));

      setTimeout(() => {
        if (data.next_problem) {
          setProblem(data.next_problem);
          setLastProblem(data.next_problem);
        }
      }, 200);
    } finally {
      setLoading(false);
    }
  };

  const loadReview = async () => {
    setLoading(true);
    try {
      setLastProblem(problem);
      const data = await safeFetch("http://127.0.0.1:8000/review");
      setReviewData(data);
      setView("review");
    } finally {
      setLoading(false);
    }
  };

  const loadRecommend = async () => {
    setLoading(true);
    try {
      setLastProblem(problem);
      const data = await safeFetch("http://127.0.0.1:8000/recommend");
      setRecommendData(data);
      setView("recommend");
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const data = await safeFetch("http://127.0.0.1:8000/analytics/summary");
      setAnalytics(data);
    } finally {
      setLoading(false);
    }
  };

  const startReviewProblem = async (problemId) => {
    setLoading(true);
    try {
      const data = await safeFetch("http://127.0.0.1:8000/practice/problem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_id: problemId }),
      });

      setProblem(data.problem || null);
      setLastProblem(data.problem || null);
      setFeedback(null);
      setSolution(null);
      setAnswer("");
      setView("practice");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Adaptive Tutor</h2>

      <button onClick={startSession} disabled={loading}>
        Start Session
      </button>
      <button onClick={loadReview} style={{ marginLeft: 8 }}>
        Review
      </button>
      <button onClick={loadRecommend} style={{ marginLeft: 8 }}>
        Recommend
      </button>
      <button onClick={loadAnalytics} style={{ marginLeft: 8 }}>
        Analytics
      </button>
      <button
        onClick={() => {
          setView("practice");
          setProblem(lastProblem);
        }}
        style={{ marginLeft: 8 }}
      >
        Back to Practice
      </button>

      {error && <div style={{ color: "red", marginTop: 12 }}>{error}</div>}

      <div style={{ marginTop: 12 }}>
        Attempts: {stats.attempts} | Accuracy:{" "}
        {stats.attempts ? ((stats.correct / stats.attempts) * 100).toFixed(1) : 0}%
      </div>

      {view === "practice" && problem && (
        <>
          <h3>{problem.title}</h3>
          <p>Difficulty: {problem.difficulty}</p>
          <p>{problem.description}</p>

          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.ctrlKey) {
                submitAnswer();
              }
            }}
          />

          <br />

          <button onClick={submitAnswer} disabled={loading}>
            {loading ? "Loading..." : "Submit"}
          </button>
        </>
      )}

      {view === "review" && (
        <div style={{ marginTop: 20 }}>
          <h3>Review Queue</h3>
          {reviewData.map((p) => (
            <div key={p.problem_id} style={{ marginBottom: 6 }}>
              {p.problem_id} - {p.status} ({p.interval}d){" "}
              <button onClick={() => startReviewProblem(p.problem_id)} disabled={loading}>
                Practice
              </button>
            </div>
          ))}
        </div>
      )}

      {view === "recommend" && (
        <div style={{ marginTop: 20 }}>
          <h3>Recommended</h3>
          {recommendData.map((p) => (
            <div key={p.problem?.problem_id || p.problem_id}>
              {p.problem?.problem_id || p.problem_id}
            </div>
          ))}
        </div>
      )}

      {view === "practice" && feedback && (
        <div style={{ marginTop: 20 }}>
          <h4>{feedback.correct ? "✅ Correct" : "❌ Incorrect"}</h4>
          <p>{feedback.hint}</p>
          {solution && <p>Solution: {solution}</p>}
          <p>Mastery: {feedback.mastery}</p>
          <p>Confidence: {feedback.confidence}</p>
        </div>
      )}

      {analytics && (
        <div style={{ marginTop: 20, borderTop: "1px solid #ddd", paddingTop: 12 }}>
          <h3>Analytics Summary</h3>
          <div>Total Attempts: {analytics.total_attempts}</div>
          <div>Accuracy: {(Number(analytics.accuracy || 0) * 100).toFixed(1)}%</div>
          <div>Avg Time: {analytics.avg_time}s</div>
          <div>Weak Topics: {(analytics.weak_topics || []).join(", ") || "None"}</div>
        </div>
      )}
    </div>
  );
}
