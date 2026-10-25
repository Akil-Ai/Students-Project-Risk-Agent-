import React, { useState, useEffect } from 'react';
import { api } from './api';
import Login from './views/Login';
import Overview from './views/Overview';
import ProjectDetails from './views/ProjectDetails';
import Alerts from './views/Alerts';
import BulkImport from './views/BulkImport';
import ModelManagement from './views/ModelManagement';
import AdminPanel from './views/AdminPanel';
import Reports from './views/Reports';

import {
  LayoutDashboard,
  FolderGit2,
  AlertOctagon,
  Upload,
  Brain,
  Sliders,
  FileBarChart2,
  LogOut,
  GraduationCap,
  ChevronRight,
  User
} from 'lucide-react';

export default function App() {
  const [user, setUser] = useState(api.getUser());
  const [currentView, setCurrentView] = useState('overview');
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  useEffect(() => {
    const savedUser = api.getUser();
    if (savedUser) {
      setUser(savedUser);
    }
  }, []);

  const handleLoginSuccess = (data) => {
    setUser({
      id: data.user_id,
      name: data.name,
      email: data.email,
      role: data.role,
    });
    setCurrentView('overview');
  };

  const handleLogout = () => {
    api.clearAuth();
    setUser(null);
    setCurrentView('overview');
    setSelectedProjectId(null);
  };

  const handleSelectProject = (id) => {
    setSelectedProjectId(id);
    setCurrentView('project-detail');
  };

  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const role = user.role;

  const navItems = [
    { key: 'overview', label: 'Cohort Overview', icon: LayoutDashboard, roles: ['admin', 'guide', 'student'] },
    { key: 'alerts', label: 'Alerts & Interventions', icon: AlertOctagon, roles: ['admin', 'guide', 'student'] },
    { key: 'import', label: 'Bulk Data Migration', icon: Upload, roles: ['admin', 'guide'] },
    { key: 'model', label: 'ML Model & Retraining', icon: Brain, roles: ['admin'] },
    { key: 'admin', label: 'System Administration', icon: Sliders, roles: ['admin'] },
    { key: 'reports', label: 'Audit Reports & Export', icon: FileBarChart2, roles: ['admin', 'guide', 'student'] },
  ].filter(item => item.roles.includes(role));

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        {/* Brand */}
        <div className="sidebar-brand">
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
          }}>
            <GraduationCap size={22} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.98rem', color: '#f8fafc', letterSpacing: '-0.02em', lineHeight: '1.2' }}>
              Risk Agent
            </div>
            <div style={{ fontSize: '0.72rem', color: '#818cf8', fontWeight: 600 }}>
              AI Decision Platform
            </div>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="sidebar-nav">
          <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#475569', padding: '10px 14px 6px' }}>
            Main Workspace
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.key;
            return (
              <div
                key={item.key}
                onClick={() => {
                  setCurrentView(item.key);
                  if (item.key !== 'project-detail') setSelectedProjectId(null);
                }}
                className={`nav-item ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} />
                <span style={{ flex: 1 }}>{item.label}</span>
                {isActive && <ChevronRight size={14} style={{ opacity: 0.6 }} />}
              </div>
            );
          })}
        </nav>

        {/* Footer User Profile & Logout */}
        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'rgba(99, 102, 241, 0.2)',
              border: '1px solid rgba(99, 102, 241, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#818cf8',
              fontWeight: 700,
              fontSize: '0.85rem'
            }}>
              {user.name.charAt(0)}
            </div>
            <div style={{ overflow: 'hidden', flex: 1 }}>
              <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.name}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'capitalize' }}>
                {user.role} Account
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="btn btn-secondary"
            style={{ width: '100%', padding: '7px 12px', fontSize: '0.78rem' }}
          >
            <LogOut size={13} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Workspace Body */}
      <main className="main-content">
        <header className="top-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.84rem' }}>Workspace</span>
            <span style={{ color: '#64748b' }}>/</span>
            <span style={{ color: '#f8fafc', fontSize: '0.84rem', fontWeight: 600, textTransform: 'capitalize' }}>
              {currentView === 'project-detail' ? `Project Details (#${selectedProjectId})` : currentView}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className={`badge ${role === 'admin' ? 'badge-high' : role === 'guide' ? 'badge-medium' : 'badge-low'}`}>
              {role.toUpperCase()}
            </span>
            <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
              {user.email}
            </div>
          </div>
        </header>

        <section className="content-body">
          {currentView === 'overview' && (
            <Overview onSelectProject={handleSelectProject} />
          )}

          {currentView === 'project-detail' && (
            <ProjectDetails
              projectId={selectedProjectId}
              onBack={() => setCurrentView('overview')}
            />
          )}

          {currentView === 'alerts' && (
            <Alerts />
          )}

          {currentView === 'import' && (
            <BulkImport />
          )}

          {currentView === 'model' && (
            <ModelManagement />
          )}

          {currentView === 'admin' && (
            <AdminPanel />
          )}

          {currentView === 'reports' && (
            <Reports />
          )}
        </section>
      </main>
    </div>
  );
}
