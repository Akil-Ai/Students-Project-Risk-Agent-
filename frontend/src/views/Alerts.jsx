import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Bell,
  AlertTriangle,
  Zap,
  CheckCircle,
  ThumbsUp,
  ThumbsDown,
  Filter,
  RefreshCw,
  Lightbulb,
  Clock
} from 'lucide-react';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [message, setMessage] = useState('');

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.getAlerts();
      setAlerts(res);
    } catch (err) {
      setMessage(`Error loading alerts: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleFeedback = async (alertId, feedback, newStatus = null) => {
    try {
      await api.sendAlertFeedback(alertId, feedback, newStatus);
      await loadAlerts();
      setMessage(`Feedback recorded: ${feedback}`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage(`Feedback error: ${err.message}`);
    }
  };

  const filteredAlerts = alerts.filter(a => {
    const matchStatus = statusFilter === 'All' ? true :
      statusFilter === 'open' ? a.status === 'open' :
      a.status !== 'open';
    const matchType = typeFilter === 'All' || a.type === typeFilter;
    return matchStatus && matchType;
  });

  const openCount = alerts.filter(a => a.status === 'open').length;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Alerts & Early Interventions
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
            Intelligent risk surge warnings, jump alerts, recommended guide actions, and feedback loop.
          </p>
        </div>
        <button onClick={loadAlerts} className="btn btn-secondary">
          <RefreshCw size={15} />
          <span>Refresh</span>
        </button>
      </div>

      {message && (
        <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#a5b4fc', marginBottom: '20px' }}>
          {message}
        </div>
      )}

      {/* KPI Cards */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
        <div className="glass-panel stat-card" style={{ '--stat-accent': '#f43f5e' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Active Open Alerts</span>
            <AlertTriangle size={20} color="#fb7185" />
          </div>
          <div className="stat-value" style={{ color: '#fb7185' }}>{openCount}</div>
          <div className="stat-subtext">Requiring faculty guide remediation</div>
        </div>

        <div className="glass-panel stat-card" style={{ '--stat-accent': '#6366f1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Total Lifetime Alerts</span>
            <Bell size={20} color="#818cf8" />
          </div>
          <div className="stat-value" style={{ color: '#ffffff' }}>{alerts.length}</div>
          <div className="stat-subtext">Logged with intelligent cooldown suppression</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel" style={{ padding: '14px 20px', marginBottom: '24px', display: 'flex', gap: '16px', alignItems: 'center' }}>
        <Filter size={16} color="#94a3b8" />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ width: '180px' }}>
          <option value="All">All Statuses</option>
          <option value="open">Open Only</option>
          <option value="resolved">Resolved / Dismissed</option>
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} style={{ width: '180px' }}>
          <option value="All">All Alert Types</option>
          <option value="HIGH_RISK">High Risk (Threshold)</option>
          <option value="RISK_JUMP">Risk Jump (Velocity)</option>
        </select>
      </div>

      {/* Alerts Feed */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '40px', color: '#94a3b8' }}>
          <RefreshCw size={28} style={{ animation: 'spin 1s linear infinite' }} />
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px 24px', textAlign: 'center' }}>
          <CheckCircle size={42} color="#34d399" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>Inbox Clean</h3>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem', marginTop: '4px' }}>
            No alerts currently match your filter criteria. All monitored cohorts are progressing smoothly!
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {filteredAlerts.map((alert) => {
            const isHigh = alert.type === 'HIGH_RISK';
            return (
              <div
                key={alert.id}
                className="glass-panel"
                style={{
                  padding: '24px',
                  borderLeft: `5px solid ${isHigh ? '#f43f5e' : '#f59e0b'}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '12px' }}>
                  <div>
                    <span style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                      #{alert.project_id} - {alert.project_title}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`badge ${isHigh ? 'badge-high' : 'badge-medium'}`}>
                      {alert.type}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: '#94a3b8', padding: '3px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.06)' }}>
                      {alert.created_at}
                    </span>
                  </div>
                </div>

                {/* Trigger Reasons */}
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                    Trigger Factors:
                  </div>
                  <ul style={{ margin: '0 0 0 18px', color: '#94a3b8', fontSize: '0.88rem' }}>
                    {alert.reasons && alert.reasons.map((r, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{r}</li>
                    ))}
                  </ul>
                </div>

                {/* Suggested Action Box */}
                <div style={{
                  padding: '12px 16px',
                  borderRadius: '10px',
                  background: 'rgba(99, 102, 241, 0.08)',
                  border: '1px dashed rgba(99, 102, 241, 0.35)',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px'
                }}>
                  <Lightbulb size={18} color="#818cf8" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <span style={{ color: '#a5b4fc', fontWeight: 600, fontSize: '0.86rem' }}>Recommended Guide Action: </span>
                    <span style={{ color: '#e0e7ff', fontSize: '0.86rem' }}>{alert.suggested_action}</span>
                  </div>
                </div>

                {/* Feedback & Status Actions */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Feedback:</span>
                    <button
                      onClick={() => handleFeedback(alert.id, 'useful')}
                      className={`btn ${alert.feedback === 'useful' ? 'btn-success' : 'btn-secondary'}`}
                      style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                    >
                      <ThumbsUp size={13} />
                      <span>Useful</span>
                    </button>
                    <button
                      onClick={() => handleFeedback(alert.id, 'not_useful')}
                      className={`btn ${alert.feedback === 'not_useful' ? 'btn-danger' : 'btn-secondary'}`}
                      style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                    >
                      <ThumbsDown size={13} />
                      <span>Not Useful</span>
                    </button>
                  </div>

                  <div>
                    {alert.status === 'open' ? (
                      <button
                        onClick={() => handleFeedback(alert.id, alert.feedback, 'resolved')}
                        className="btn btn-success"
                        style={{ padding: '5px 14px', fontSize: '0.8rem' }}
                      >
                        <CheckCircle size={14} />
                        <span>Mark as Resolved</span>
                      </button>
                    ) : (
                      <span className="badge badge-low" style={{ textTransform: 'capitalize' }}>
                        {alert.status}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
