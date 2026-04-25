import React, { useState } from 'react';

export default function SignupForm({ onComplete }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    years_coding: '0',
    dsa_experience: 'none',
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.name.length < 2 || formData.password.length < 8) {
      setError("Please fill out Name and secure Password");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          years_coding: parseInt(formData.years_coding, 10),
        }),
      });
      const data = await response.json();
      if (response.ok) {
        onComplete(data.userProfile, data.user_id);
      } else {
        setError("Error during signup");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl mb-4 font-bold">Step 1: Sign Up</h2>
      {error && <div className="text-red-400 mb-2">{error}</div>}
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <input className="p-2 bg-slate-700 rounded" placeholder="Full Name" type="text" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required />
        <input className="p-2 bg-slate-700 rounded" placeholder="Email Address" type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} required />
        <input className="p-2 bg-slate-700 rounded" placeholder="Password (min 8 chars)" type="password" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} required />
        
        <select className="p-2 bg-slate-700 rounded" value={formData.years_coding} onChange={e => setFormData({ ...formData, years_coding: e.target.value })}>
          <option value="0">Years Coding: None</option>
          <option value="1">1 Year</option>
          <option value="3">3 Years</option>
          <option value="5">5+ Years</option>
        </select>
        
        <div className="flex gap-4">
          <span>DSA Experience:</span>
          {['none', 'little', 'some', 'experienced'].map(exp => (
            <label key={exp} className="flex items-center gap-1 cursor-pointer">
              <input type="radio" name="dsa_experience" value={exp} checked={formData.dsa_experience === exp} onChange={e => setFormData({ ...formData, dsa_experience: e.target.value })} />
              {exp}
            </label>
          ))}
        </div>
        
        <button disabled={loading} type="submit" className="mt-4 p-3 bg-blue-600 hover:bg-blue-500 rounded font-semibold transition-colors">
          {loading ? "Signing up..." : "Continue"}
        </button>
      </form>
    </div>
  );
}
