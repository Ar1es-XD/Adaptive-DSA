import React from 'react';
import { Link } from 'react-router-dom';

const highlights = [
  {
    title: 'Adaptive Learning Path',
    description: 'Start with a quick diagnostic and receive a personalized sequence of DSA topics built around your strengths and gaps.',
  },
  {
    title: 'Hands-on Problem Solving',
    description: 'Practice with guided coding challenges and immediate feedback to reinforce the right patterns and techniques.',
  },
  {
    title: 'Track Real Progress',
    description: 'See your momentum clearly with topic-level analytics, streaks, and milestone-based achievements.',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="sticky top-0 z-10 border-b border-slate-800/90 bg-slate-950/90 backdrop-blur">
        <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="text-lg font-semibold tracking-wide text-cyan-300">Adaptive DSA</div>
          <Link
            to="/onboarding"
            className="rounded-md border border-cyan-400/40 px-4 py-2 text-sm font-medium text-cyan-200 transition hover:border-cyan-300 hover:bg-cyan-400/10"
          >
            Get Started
          </Link>
        </nav>
      </header>

      <main className="mx-auto grid w-full max-w-6xl gap-12 px-6 pb-20 pt-16 md:grid-cols-2 md:items-center md:py-24">
        <section>
          <p className="mb-4 inline-flex rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-1 text-xs font-semibold uppercase tracking-wider text-cyan-200">
            Learn smarter, not harder
          </p>
          <h1 className="text-4xl font-bold leading-tight text-white md:text-5xl">
            Master Data Structures & Algorithms with an Adaptive Coach
          </h1>
          <p className="mt-6 max-w-xl text-lg text-slate-300">
            Adaptive DSA creates a personalized roadmap, evaluates your growth, and guides each next step so you spend time where it matters most.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              to="/onboarding"
              className="rounded-md bg-cyan-400 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
            >
              Start Free Assessment
            </Link>
            <Link
              to="/dashboard"
              className="rounded-md border border-slate-600 px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-400 hover:bg-slate-800"
            >
              View Demo Dashboard
            </Link>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900 to-slate-950 p-6 shadow-2xl shadow-cyan-900/20">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-cyan-200">Why students choose Adaptive DSA</h2>
            <span className="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-medium text-emerald-300">Live Progress</span>
          </div>
          <div className="space-y-4">
            {highlights.map((item) => (
              <article key={item.title} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                <h3 className="text-base font-semibold text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-300">{item.description}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
