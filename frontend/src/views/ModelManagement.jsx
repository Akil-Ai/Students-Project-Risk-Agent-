import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  BrainCircuit,
  Cpu,
  RefreshCw,
  Sliders,
  CheckCircle2,
  Award,
  Zap,
  Activity
} from 'lucide-react';

export default function ModelManagement() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getModels();
      setData(res);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to load model registry');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRetrain = async () => {
    setTraining(true);
    setError('');
    setMessage('');
    try {
      const res = await api.retrainModel();
      setMessage(`Model successfully retrained! Version: ${res.result?.version || 'Updated'}`);
      await loadData();
    } catch (err) {
      setError(`Retraining error: ${err.message}`);
    } finally {
      setTraining(false);
    }
  };

  if (loading && !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#94a3b8' }}>
        <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite' }} />
      </div>
    );
  }

  const active = data?.active_model;
  const metrics = active?.metrics || {};

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            ML Model Management & Retraining
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
            LightGBM binary classifier, SHAP tree explainability, target recall optimization & versioning.
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

      {message && (
        <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399', marginBottom: '24px' }}>
          {message}
        </div>
      )}

      {/* KPI Cards */}
      <div className="stat-grid">
        <div className="glass-panel stat-card" style={{ '--stat-accent': '#6366f1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Completed Training Samples</span>
            <BrainCircuit size={20} color="#818cf8" />
          </div>
          <div className="stat-value" style={{ color: '#ffffff' }}>{data?.completed_count || 0}</div>
          <div className="stat-subtext">Min required: {data?.min_required || 15} projects</div>
        </div>

        <div className="glass-panel stat-card" style={{ '--stat-accent': '#06b6d4' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Active Scorer Engine</span>
            <Cpu size={20} color="#22d3ee" />
          </div>
          <div className="stat-value" style={{ fontSize: '1.4rem', color: '#22d3ee', marginTop: '12px' }}>
            {active?.version || 'Rule-Based Engine'}
          </div>
          <div className="stat-subtext">{active?.trained_at ? `Trained: ${active.trained_at}` : 'Cold-start mode'}</div>
        </div>

        <div className="glass-panel stat-card" style={{ '--stat-accent': '#10b981' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Target Recall Policy</span>
            <Award size={20} color="#34d399" />
          </div>
          <div className="stat-value" style={{ color: '#34d399' }}>
            {data?.target_recall ? `${(data.target_recall * 100).toFixed(0)}%` : '85%'}
          </div>
          <div className="stat-subtext">Threshold tuned to catch genuine risks</div>
        </div>
      </div>

      {/* Retrain Action Card */}
      <div className="glass-panel" style={{ padding: '28px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
          <div style={{ maxWidth: '600px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
              Trigger Offline / Live Model Retraining
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem' }}>
              Partitions historical projects using semester splits, calculates SHAP feature importances, applies class weights, and saves a timestamped model artifact into the store.
            </p>
          </div>
          <button
            onClick={handleRetrain}
            disabled={training}
            className="btn btn-primary"
            style={{ padding: '12px 24px', fontSize: '0.95rem' }}
          >
            <Zap size={18} className={training ? 'spin' : ''} />
            <span>{training ? 'Training Model...' : 'Retrain LightGBM Model'}</span>
          </button>
        </div>
      </div>

      {/* Validation Performance Metrics */}
      {metrics && Object.keys(metrics).length > 0 && (
        <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="#818cf8" />
            <span>Active Model Validation Metrics</span>
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            {Object.entries(metrics).map(([k, v]) => (
              <div key={k} style={{ padding: '16px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8' }}>
                  {k.replace('_', ' ')}
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
                  {typeof v === 'number' ? (v < 1 ? (v * 100).toFixed(1) + '%' : v.toFixed(2)) : String(v)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historical Model Versions */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '16px' }}>
          Trained Model Registry
        </h3>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Version ID</th>
                <th>Trained At</th>
                <th>Status</th>
                <th>ROC-AUC</th>
                <th>Recall</th>
                <th>Precision</th>
              </tr>
            </thead>
            <tbody>
              {data?.all_models && data.all_models.length > 0 ? (
                data.all_models.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, color: '#818cf8' }}>
                      {m.version}
                    </td>
                    <td>{m.trained_at}</td>
                    <td>
                      {m.is_active ? (
                        <span className="badge badge-low">Active Production</span>
                      ) : (
                        <span className="badge badge-unscored">Archived</span>
                      )}
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                      {m.metrics?.roc_auc ? (m.metrics.roc_auc * 100).toFixed(1) + '%' : '-'}
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                      {m.metrics?.recall ? (m.metrics.recall * 100).toFixed(1) + '%' : '-'}
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                      {m.metrics?.precision ? (m.metrics.precision * 100).toFixed(1) + '%' : '-'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                    No trained model versions in store. Click "Retrain LightGBM Model" above to train the first production version.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
