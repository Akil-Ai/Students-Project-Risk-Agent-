import React, { useState } from 'react';
import { api } from '../api';
import { ShieldCheck, Mail, Lock, ArrowRight, Sparkles, GraduationCap } from 'lucide-react';

export default function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide both institutional email and password.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const data = await api.login(email, password);
      onLoginSuccess(data);
    } catch (err) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillQuick = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'radial-gradient(circle at 50% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 60%), #0a0f1d',
    }}>
      <div style={{ maxWidth: '440px', width: '100%' }}>
        {/* Logo / Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '64px',
            height: '64px',
            borderRadius: '20px',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(6, 182, 212, 0.2))',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            boxShadow: '0 0 30px rgba(99, 102, 241, 0.3)',
            marginBottom: '16px',
            color: '#818cf8'
          }}>
            <GraduationCap size={36} />
          </div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#f8fafc' }}>
            Student Project Risk Agent
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem', marginTop: '6px' }}>
            Predictive ML early-warning system and intervention agent for academic project teams.
          </p>
        </div>

        {/* Card */}
        <div className="glass-panel" style={{ padding: '32px 36px' }}>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>Sign In</h2>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem', marginTop: '2px' }}>
              Access role-based analytics, interventions & progress.
            </p>
          </div>

          {error && (
            <div style={{
              background: 'rgba(244, 63, 94, 0.12)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              borderRadius: '8px',
              padding: '12px 14px',
              color: '#fb7185',
              fontSize: '0.85rem',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>⚠️ {error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                Institutional Email
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} style={{ position: 'absolute', left: '12px', top: '13px', color: '#64748b' }} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@college.edu or guide1@college.edu"
                  style={{ paddingLeft: '38px' }}
                  required
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} style={{ position: 'absolute', left: '12px', top: '13px', color: '#64748b' }} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  style={{ paddingLeft: '38px' }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', marginTop: '8px', padding: '12px' }}
            >
              {loading ? 'Authenticating...' : (
                <>
                  <span>Sign In to Portal</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Acccount Helper */}
          <div style={{
            marginTop: '28px',
            paddingTop: '20px',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.8rem',
            color: '#94a3b8'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px', color: '#cbd5e1', fontWeight: 600 }}>
              <Sparkles size={14} color="#818cf8" />
              <span>Quick Demo Accounts:</span>
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                onClick={() => fillQuick('admin@college.edu', 'Admin@123456')}
              >
                Admin
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                onClick={() => fillQuick('guide1@college.edu', 'Password@123')}
              >
                Guide
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                onClick={() => fillQuick('student1@college.edu', 'Password@123')}
              >
                Student
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
