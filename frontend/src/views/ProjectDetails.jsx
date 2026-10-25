import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  ArrowLeft,
  RefreshCw,
  Target,
  FileText,
  Calendar,
  CheckCircle2,
  Clock,
  AlertCircle,
  Plus,
  Send,
  User,
  Users,
  Sparkles,
  TrendingUp
} from 'lucide-react';

export default function ProjectDetails({ projectId, onBack }) {
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [activeTab, setActiveTab] = useState('risk');
  const [userRole, setUserRole] = useState('student');
  const [message, setMessage] = useState('');

  // Form states
  const [reviewForm, setReviewForm] = useState({
    review_date: new Date().toISOString().split('T')[0],
    rubric_presentation: 8,
    rubric_code: 7,
    rubric_viva: 5,
    attendance: 1.0,
    reviewer_comment: '',
    action_items_summary: '',
    action_item_desc: '',
    action_item_due: new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0]
  });

  const [progressForm, setProgressForm] = useState({
    week_start: new Date().toISOString().split('T')[0],
    milestone_completion_pct: 25,
    commits_or_updates: 5,
    missed_meetings: 0,
    deadline_slips: 0,
    notes: ''
  });

  const loadProject = async () => {
    setLoading(true);
    try {
      const u = api.getUser();
      if (u) setUserRole(u.role);
      const res = await api.getProjectDetails(projectId);
      setProject(res);
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) loadProject();
  }, [projectId]);

  const handleRecalculateRisk = async () => {
    setRecalculating(true);
    try {
      await api.recalculateRisk(projectId);
      await loadProject();
      setMessage('Risk score successfully recalculated.');
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      setMessage(`Recalculation error: ${err.message}`);
    } finally {
      setRecalculating(false);
    }
  };

  const handleConductReview = async (e) => {
    e.preventDefault();
    try {
      await api.addReview(projectId, reviewForm);
      await loadProject();
      setMessage('Project review and action items successfully logged!');
      setReviewForm({
        ...reviewForm,
        reviewer_comment: '',
        action_items_summary: '',
        action_item_desc: ''
      });
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      setMessage(`Review error: ${err.message}`);
    }
  };

  const handleSubmitProgress = async (e) => {
    e.preventDefault();
    try {
      await api.addProgressLog(projectId, progressForm);
      await loadProject();
      setMessage('Weekly progress report logged successfully!');
      setProgressForm({ ...progressForm, notes: '' });
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      setMessage(`Progress submission error: ${err.message}`);
    }
  };

  const handleUpdateActionItem = async (itemId, newStatus) => {
    try {
      await api.updateActionItem(itemId, newStatus);
      await loadProject();
    } catch (err) {
      setMessage(`Action item update failed: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', color: '#94a3b8' }}>
        <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite' }} />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
        <h3>Project not found</h3>
        <button onClick={onBack} className="btn btn-secondary" style={{ marginTop: '16px' }}>
          Back to Overview
        </button>
      </div>
    );
  }

  const latestRisk = project.latest_risk;
  const riskHistory = project.risk_history || [];

  return (
    <div>
      {/* Top back nav */}
      <button onClick={onBack} className="btn btn-secondary" style={{ marginBottom: '16px' }}>
        <ArrowLeft size={16} />
        <span>Back to Cohort Overview</span>
      </button>

      {/* Project Header Banner */}
      <div className="glass-panel" style={{ padding: '28px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', color: '#818cf8', fontWeight: 700, fontSize: '1rem' }}>
                #{project.id}
              </span>
              <span className={`badge ${latestRisk?.bucket === 'High' ? 'badge-high' : latestRisk?.bucket === 'Medium' ? 'badge-medium' : 'badge-low'}`}>
                {latestRisk?.bucket || 'Unscored'} Risk
              </span>
              <span style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.08)' }}>
                {project.type} Project
              </span>
            </div>
            <h1 style={{ fontSize: '1.7rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
              {project.title}
            </h1>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginTop: '14px', fontSize: '0.86rem', color: '#cbd5e1' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <User size={15} color="#818cf8" />
                <span>Guide: <b>{project.guide_name}</b></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Users size={15} color="#818cf8" />
                <span>Team: <b>{project.team_size} members</b></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Calendar size={15} color="#818cf8" />
                <span>Schedule: <b>{project.start_date} → {project.planned_end_date}</b></span>
              </div>
            </div>
          </div>

          <button
            onClick={handleRecalculateRisk}
            disabled={recalculating}
            className="btn btn-primary"
            style={{ padding: '10px 18px' }}
          >
            <RefreshCw size={16} className={recalculating ? 'spin' : ''} />
            <span>{recalculating ? 'Scoring...' : 'Recalculate Risk Now'}</span>
          </button>
        </div>
      </div>

      {message && (
        <div style={{ padding: '12px 18px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#a5b4fc', marginBottom: '20px' }}>
          {message}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '24px' }}>
        {[
          { key: 'risk', label: 'Risk & SHAP Explainability', icon: Sparkles },
          { key: 'milestones', label: 'Milestones & Burndown', icon: Target },
          { key: 'reviews', label: 'Reviews & Action Items', icon: FileText },
          { key: 'progress', label: 'Weekly Progress Logs', icon: TrendingUp }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 20px',
                background: 'none',
                border: 'none',
                borderBottom: isActive ? '2px solid #6366f1' : '2px solid transparent',
                color: isActive ? '#ffffff' : '#94a3b8',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.9rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <Icon size={16} color={isActive ? '#818cf8' : '#94a3b8'} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT: RISK & SHAP */}
      {activeTab === 'risk' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          {/* Current Risk Card */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={18} color="#818cf8" />
              <span>Current Assessment Metrics</span>
            </h3>

            {latestRisk ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '16px' }}>
                  <span style={{ fontSize: '2.5rem', fontWeight: 800, color: latestRisk.probability > 0.5 ? '#fb7185' : '#34d399', fontFamily: 'JetBrains Mono, monospace' }}>
                    {(latestRisk.probability * 100).toFixed(1)}%
                  </span>
                  <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Predicted Delay Probability</span>
                </div>

                <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)', marginBottom: '20px' }}>
                  <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Active Scorer Engine:</div>
                  <div style={{ fontWeight: 600, color: '#f8fafc', marginTop: '2px' }}>{latestRisk.model_version}</div>
                </div>

                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '10px' }}>
                  Top Delay Contributors (Explainability)
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {latestRisk.top_factors && latestRisk.top_factors.length > 0 ? (
                    latestRisk.top_factors.map((f, i) => (
                      <div
                        key={i}
                        style={{
                          padding: '12px 14px',
                          borderRadius: '8px',
                          background: 'rgba(244, 63, 94, 0.08)',
                          border: '1px solid rgba(244, 63, 94, 0.2)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <span style={{ fontSize: '0.86rem', color: '#f8fafc' }}>{f.description || JSON.stringify(f)}</span>
                        {f.impact && (
                          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#fb7185', background: 'rgba(244, 63, 94, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                            +{f.impact.toFixed(2)}
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No significant risk flags registered.</p>
                  )}
                </div>
              </div>
            ) : (
              <p style={{ color: '#94a3b8' }}>No score calculated yet. Click "Recalculate Risk Now" above.</p>
            )}
          </div>

          {/* Historical Trajectory */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TrendingUp size={18} color="#818cf8" />
              <span>Historical Risk Trajectory ({riskHistory.length} Scores)</span>
            </h3>

            {riskHistory.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {riskHistory.map((h) => (
                  <div
                    key={h.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle)'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>{h.date}</div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b' }}>Model: {h.model_version}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className={`badge ${h.bucket === 'High' ? 'badge-high' : h.bucket === 'Medium' ? 'badge-medium' : 'badge-low'}`}>
                        {h.bucket}
                      </span>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: '#f8fafc' }}>
                        {(h.probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>No history recorded yet.</p>
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: MILESTONES */}
      {activeTab === 'milestones' && (
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '18px' }}>
            Scheduled Milestones & Target Completion
          </h3>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Milestone Name</th>
                  <th>Target Date</th>
                  <th>Planned Cumulative %</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {project.milestones && project.milestones.length > 0 ? (
                  project.milestones.map((m) => (
                    <tr key={m.id}>
                      <td style={{ fontWeight: 600, color: '#ffffff' }}>{m.name}</td>
                      <td>{m.planned_date}</td>
                      <td style={{ fontFamily: 'JetBrains Mono, monospace' }}>{m.planned_pct}%</td>
                      <td>
                        {m.completed_date ? (
                          <span className="badge badge-low">Completed ({m.completed_date})</span>
                        ) : (
                          <span className="badge badge-medium">Pending Execution</span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                      No milestones registered for this project yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT: REVIEWS & ACTION ITEMS */}
      {activeTab === 'reviews' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Guide Conduct Review Form */}
          {['admin', 'guide'].includes(userRole) && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus size={18} color="#818cf8" />
                <span>Conduct Formal Project Review</span>
              </h3>
              <form onSubmit={handleConductReview} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Review Date</label>
                  <input
                    type="date"
                    value={reviewForm.review_date}
                    onChange={(e) => setReviewForm({ ...reviewForm, review_date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Presentation Score (0-10)</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={reviewForm.rubric_presentation}
                    onChange={(e) => setReviewForm({ ...reviewForm, rubric_presentation: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Code / Impl Score (0-10)</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={reviewForm.rubric_code}
                    onChange={(e) => setReviewForm({ ...reviewForm, rubric_code: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Viva / Q&A Score (0-10)</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={reviewForm.rubric_viva}
                    onChange={(e) => setReviewForm({ ...reviewForm, rubric_viva: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Attendance Ratio (0.0 - 1.0)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={reviewForm.attendance}
                    onChange={(e) => setReviewForm({ ...reviewForm, attendance: parseFloat(e.target.value) || 1.0 })}
                  />
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Reviewer Comments / Observations</label>
                  <textarea
                    rows="2"
                    value={reviewForm.reviewer_comment}
                    onChange={(e) => setReviewForm({ ...reviewForm, reviewer_comment: e.target.value })}
                    placeholder="Progress notes, architectural feedback, or blockers noticed..."
                  />
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Mandatory Action Item Description</label>
                  <input
                    type="text"
                    value={reviewForm.action_item_desc}
                    onChange={(e) => setReviewForm({ ...reviewForm, action_item_desc: e.target.value })}
                    placeholder="e.g., Deliver complete REST API swagger documentation and unit test suite"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Action Item Due Date</label>
                  <input
                    type="date"
                    value={reviewForm.action_item_due}
                    onChange={(e) => setReviewForm({ ...reviewForm, action_item_due: e.target.value })}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                  <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '11px' }}>
                    <Send size={15} />
                    <span>Submit Review & Score</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Action Items List */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>
              Action Items & Remediation Directives
            </h3>
            {project.action_items && project.action_items.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {project.action_items.map((ai) => (
                  <div
                    key={ai.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '14px 18px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle)',
                      flexWrap: 'wrap',
                      gap: '12px'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: '#f8fafc' }}>{ai.description}</div>
                      <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
                        Due by: {ai.due_date} • Status: <span style={{ textTransform: 'capitalize' }}>{ai.status}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {ai.status !== 'completed' && (
                        <button
                          onClick={() => handleUpdateActionItem(ai.id, 'completed')}
                          className="btn btn-success"
                          style={{ padding: '5px 12px', fontSize: '0.78rem' }}
                        >
                          <CheckCircle2 size={13} />
                          <span>Mark Complete</span>
                        </button>
                      )}
                      {ai.status === 'completed' && (
                        <button
                          onClick={() => handleUpdateActionItem(ai.id, 'pending')}
                          className="btn btn-secondary"
                          style={{ padding: '5px 12px', fontSize: '0.78rem' }}
                        >
                          Reopen
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>No action items recorded for this project.</p>
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: WEEKLY PROGRESS */}
      {activeTab === 'progress' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Progress Submission Form */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Plus size={18} color="#818cf8" />
              <span>Submit Weekly Progress Log</span>
            </h3>
            <form onSubmit={handleSubmitProgress} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Week Starting Date</label>
                <input
                  type="date"
                  value={progressForm.week_start}
                  onChange={(e) => setProgressForm({ ...progressForm, week_start: e.target.value })}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Milestone Progress % (0-100)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={progressForm.milestone_completion_pct}
                  onChange={(e) => setProgressForm({ ...progressForm, milestone_completion_pct: parseFloat(e.target.value) || 0 })}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Commits / Deliverables</label>
                <input
                  type="number"
                  min="0"
                  value={progressForm.commits_or_updates}
                  onChange={(e) => setProgressForm({ ...progressForm, commits_or_updates: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Missed Meetings</label>
                <input
                  type="number"
                  min="0"
                  value={progressForm.missed_meetings}
                  onChange={(e) => setProgressForm({ ...progressForm, missed_meetings: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Deadline Slips</label>
                <input
                  type="number"
                  min="0"
                  value={progressForm.deadline_slips}
                  onChange={(e) => setProgressForm({ ...progressForm, deadline_slips: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Weekly Progress Summary & Impediments</label>
                <textarea
                  rows="2"
                  value={progressForm.notes}
                  onChange={(e) => setProgressForm({ ...progressForm, notes: e.target.value })}
                  placeholder="Completed user authentication module, backend unit tests passing..."
                />
              </div>
              <div>
                <button type="submit" className="btn btn-primary" style={{ padding: '10px 20px' }}>
                  <Send size={15} />
                  <span>Log Progress</span>
                </button>
              </div>
            </form>
          </div>

          {/* Past Progress History Table */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>
              Progress Submission Timeline
            </h3>
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Week Start</th>
                    <th>Milestone Progress</th>
                    <th>Commits/Updates</th>
                    <th>Missed Meetings</th>
                    <th>Deadline Slips</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {project.progress_logs && project.progress_logs.length > 0 ? (
                    project.progress_logs.map((pl) => (
                      <tr key={pl.id}>
                        <td style={{ fontFamily: 'JetBrains Mono, monospace' }}>{pl.week_start}</td>
                        <td style={{ fontWeight: 600, color: '#34d399' }}>{pl.milestone_completion_pct}%</td>
                        <td>{pl.commits_or_updates}</td>
                        <td style={{ color: pl.missed_meetings > 0 ? '#fb7185' : '#cbd5e1' }}>{pl.missed_meetings}</td>
                        <td style={{ color: pl.deadline_slips > 0 ? '#fb7185' : '#cbd5e1' }}>{pl.deadline_slips}</td>
                        <td style={{ color: '#94a3b8', fontSize: '0.85rem' }}>{pl.notes || '-'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                        No weekly progress logs submitted yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
