import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Settings,
  Users,
  Clock,
  UserPlus,
  Save,
  CheckCircle,
  RefreshCw,
  Server
} from 'lucide-react';

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [settings, setSettings] = useState({});
  const [scheduler, setScheduler] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // User form
  const [userForm, setUserForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'guide',
    department: 'Computer Science',
    usn_or_roll: ''
  });

  const loadAll = async () => {
    setLoading(true);
    try {
      const [u, s, sc] = await Promise.all([
        api.getUsers(),
        api.getSettings(),
        api.getScheduler()
      ]);
      setUsers(u);
      setSettings(s);
      setScheduler(sc);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await api.createUser(userForm);
      setMessage(`User ${userForm.email} created successfully!`);
      setUserForm({
        name: '',
        email: '',
        password: '',
        role: 'guide',
        department: 'Computer Science',
        usn_or_roll: ''
      });
      await loadAll();
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      setError(`Creation error: ${err.message}`);
    }
  };

  const handleUpdateSetting = async (key, val) => {
    try {
      let parsedVal = val;
      try {
        parsedVal = JSON.parse(val);
      } catch {
        // use as string/number
      }
      await api.updateSetting(key, parsedVal);
      setMessage(`Saved setting: ${key}`);
      await loadAll();
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(`Setting update error: ${err.message}`);
    }
  };

  if (loading && users.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#94a3b8' }}>
        <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite' }} />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            System Administration & Control
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
            Role-based user provisioning, runtime configuration override, and APScheduler background heartbeat.
          </p>
        </div>
        <button onClick={loadAll} className="btn btn-secondary">
          <RefreshCw size={15} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fb7185', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      {message && (
        <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', marginBottom: '24px' }}>
          {message}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '24px' }}>
        {[
          { key: 'users', label: 'User Provisioning & Directory', icon: Users },
          { key: 'settings', label: 'Live Runtime Settings', icon: Settings },
          { key: 'scheduler', label: 'Scheduler Heartbeat', icon: Clock }
        ].map(tab => {
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
                cursor: 'pointer'
              }}
            >
              <Icon size={16} color={isActive ? '#818cf8' : '#94a3b8'} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB: USERS */}
      {activeTab === 'users' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Create User */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <UserPlus size={18} color="#818cf8" />
              <span>Create New User Account</span>
            </h3>
            <form onSubmit={handleCreateUser} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Dr. Jane Foster"
                  value={userForm.name}
                  onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Institutional Email</label>
                <input
                  type="email"
                  placeholder="e.g. jfoster@college.edu"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Temporary Password</label>
                <input
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>User Role</label>
                <select value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
                  <option value="guide">Faculty Guide</option>
                  <option value="student">Student Scholar</option>
                  <option value="admin">System Administrator</option>
                </select>
              </div>

              {userForm.role === 'guide' && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>Department</label>
                  <input
                    type="text"
                    value={userForm.department}
                    onChange={(e) => setUserForm({ ...userForm, department: e.target.value })}
                  />
                </div>
              )}

              {userForm.role === 'student' && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '4px' }}>USN / Roll Number</label>
                  <input
                    type="text"
                    placeholder="e.g. 1MS22CS045"
                    value={userForm.usn_or_roll}
                    onChange={(e) => setUserForm({ ...userForm, usn_or_roll: e.target.value })}
                  />
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '11px' }}>
                  <UserPlus size={15} />
                  <span>Provision Account</span>
                </button>
              </div>
            </form>
          </div>

          {/* User Directory */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '16px' }}>
              Institutional User Directory ({users.length})
            </h3>
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>User ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Department / USN</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td style={{ fontFamily: 'JetBrains Mono, monospace', color: '#818cf8' }}>#{u.id}</td>
                      <td style={{ fontWeight: 600, color: '#f8fafc' }}>{u.name}</td>
                      <td>{u.email}</td>
                      <td>
                        <span className={`badge ${u.role === 'admin' ? 'badge-high' : u.role === 'guide' ? 'badge-medium' : 'badge-low'}`}>
                          {u.role.toUpperCase()}
                        </span>
                      </td>
                      <td>{u.department || u.usn || '-'}</td>
                      <td>{u.created_at || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB: SETTINGS */}
      {activeTab === 'settings' && (
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '16px' }}>
            Runtime System Configuration (Synchronized with Database)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {Object.entries(settings).map(([k, v]) => {
              const valStr = typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v);
              return (
                <div
                  key={k}
                  style={{
                    padding: '16px 20px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}
                >
                  <div style={{ flex: '1', minWidth: '240px' }}>
                    <div style={{ fontWeight: 600, color: '#818cf8', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.9rem' }}>
                      {k}
                    </div>
                    <input
                      type="text"
                      defaultValue={valStr}
                      id={`setting-${k}`}
                      style={{ marginTop: '6px', fontSize: '0.85rem' }}
                    />
                  </div>
                  <button
                    onClick={() => {
                      const inputElem = document.getElementById(`setting-${k}`);
                      if (inputElem) handleUpdateSetting(k, inputElem.value);
                    }}
                    className="btn btn-secondary"
                    style={{ padding: '8px 16px', fontSize: '0.8rem' }}
                  >
                    <Save size={14} />
                    <span>Save Key</span>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB: SCHEDULER */}
      {activeTab === 'scheduler' && (
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={18} color="#818cf8" />
            <span>APScheduler Background Daemon Heartbeat</span>
          </h3>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Daemon Status:</span>
            {scheduler?.running ? (
              <span className="badge badge-low">Operational & Running</span>
            ) : (
              <span className="badge badge-high">Stopped</span>
            )}
          </div>

          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '12px' }}>
            Registered Scheduled Jobs
          </h4>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Task Name</th>
                  <th>Next Execution Schedule</th>
                </tr>
              </thead>
              <tbody>
                {scheduler?.jobs && scheduler.jobs.length > 0 ? (
                  scheduler.jobs.map(j => (
                    <tr key={j.id}>
                      <td style={{ fontFamily: 'JetBrains Mono, monospace', color: '#818cf8' }}>{j.id}</td>
                      <td>{j.name}</td>
                      <td>{j.next_run_time}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" style={{ textAlign: 'center', padding: '20px', color: '#94a3b8' }}>
                      No background jobs currently registered in APScheduler.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
