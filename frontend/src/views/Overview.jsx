import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  FolderKanban,
  AlertTriangle,
  Clock,
  CheckCircle,
  TrendingUp,
  Search,
  Filter,
  ArrowUpRight,
  RefreshCw
} from 'lucide-react';

export default function Overview({ onSelectProject }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [search, setSearch] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('All');
  const [riskFilter, setRiskFilter] = useState('All');

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getOverview();
      setData(res);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to fetch overview data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', color: '#94a3b8' }}>
        <RefreshCw className="spin" size={32} style={{ animation: 'spin 1s linear infinite' }} />
      </div>
    );
  }

  const projects = data?.projects || [];

  // Filter projects
  const semesters = ['All', ...new Set(projects.map(p => p.semester))];
  const filtered = projects.filter(p => {
    const matchSearch = p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.guide_name.toLowerCase().includes(search.toLowerCase());
    const matchSem = semesterFilter === 'All' || p.semester === semesterFilter;
    const matchRisk = riskFilter === 'All' || p.risk_bucket === riskFilter;
    return matchSearch && matchSem && matchRisk;
  });

  const getBadgeClass = (bucket) => {
    if (bucket === 'High') return 'badge badge-high';
    if (bucket === 'Medium') return 'badge badge-medium';
    if (bucket === 'Low') return 'badge badge-low';
    return 'badge badge-unscored';
  };

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Project Progress & Risk Overview
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
            Real-time multi-factor ML risk predictions and completion probability metrics across active cohorts.
          </p>
        </div>
        <button onClick={loadData} className="btn btn-secondary">
          <RefreshCw size={15} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fb7185', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      {/* KPI Stat Cards */}
      <div className="stat-grid">
        <div className="glass-panel stat-card" style={{ '--stat-accent': '#6366f1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Monitored Projects</span>
            <FolderKanban size={20} color="#818cf8" />
          </div>
          <div className="stat-value" style={{ color: '#ffffff' }}>{data?.total_projects || 0}</div>
          <div className="stat-subtext">Across assigned semesters</div>
        </div>

        <div className="glass-panel stat-card" style={{ '--stat-accent': '#f43f5e' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">High Risk (Urgent)</span>
            <AlertTriangle size={20} color="#fb7185" />
          </div>
          <div className="stat-value" style={{ color: '#fb7185' }}>{data?.high_risk_count || 0}</div>
          <div className="stat-subtext">Severe delay probability predicted</div>
        </div>

        <div className="glass-panel stat-card" style={{ '--stat-accent': '#f59e0b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Medium Risk (Watch)</span>
            <Clock size={20} color="#fbbf24" />
          </div>
          <div className="stat-value" style={{ color: '#fbbf24' }}>{data?.medium_risk_count || 0}</div>
          <div className="stat-subtext">Milestone or attendance lag</div>
        </div>

        <div className="glass-panel stat-card" style={{ '--stat-accent': '#10b981' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Low Risk (On Track)</span>
            <CheckCircle size={20} color="#34d399" />
          </div>
          <div className="stat-value" style={{ color: '#34d399' }}>{data?.low_risk_count || 0}</div>
          <div className="stat-subtext">Meeting schedule deadlines</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1', minWidth: '220px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
          <input
            type="text"
            placeholder="Search by project title or guide name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: '36px' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Filter size={15} color="#94a3b8" />
          <select value={semesterFilter} onChange={(e) => setSemesterFilter(e.target.value)} style={{ width: '150px' }}>
            {semesters.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)} style={{ width: '150px' }}>
            <option value="All">All Risk Levels</option>
            <option value="High">High Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="Low">Low Risk</option>
            <option value="Unscored">Unscored</option>
          </select>
        </div>
      </div>

      {/* Projects Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
            Cohort Project Registry ({filtered.length})
          </h2>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Click any project row to open deep inspection</span>
        </div>

        <div className="data-table-container" style={{ border: 'none', borderRadius: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Project Title</th>
                <th>Type</th>
                <th>Semester</th>
                <th>Assigned Guide</th>
                <th>Risk Level</th>
                <th>Delay Prob</th>
                <th>Primary Risk Driver</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
                    No matching projects found for your filter criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((proj) => (
                  <tr
                    key={proj.id}
                    onClick={() => onSelectProject(proj.id)}
                    style={{ cursor: 'pointer', transition: 'background 0.15s' }}
                  >
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', color: '#818cf8', fontWeight: 600 }}>
                      #{proj.id}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: '#ffffff' }}>{proj.title}</div>
                      <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Target: {proj.planned_end_date}</div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.82rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.06)' }}>
                        {proj.type}
                      </span>
                    </td>
                    <td>{proj.semester}</td>
                    <td style={{ color: '#cbd5e1' }}>{proj.guide_name}</td>
                    <td>
                      <span className={getBadgeClass(proj.risk_bucket)}>
                        {proj.risk_bucket}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, color: proj.delay_probability > 0.5 ? '#fb7185' : '#34d399' }}>
                      {proj.delay_probability !== null ? `${(proj.delay_probability * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td style={{ maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#94a3b8', fontSize: '0.84rem' }}>
                      {proj.top_factor}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectProject(proj.id);
                        }}
                      >
                        <span>Details</span>
                        <ArrowUpRight size={13} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
