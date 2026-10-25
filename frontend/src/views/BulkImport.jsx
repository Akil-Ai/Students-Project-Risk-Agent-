import React, { useState } from 'react';
import { api } from '../api';
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  CheckCircle,
  AlertCircle,
  FileText
} from 'lucide-react';

export default function BulkImport() {
  const [entityType, setEntityType] = useState('projects');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleDownloadTemplate = () => {
    window.open(`${api.getBaseUrl()}/import/template/${entityType}`, '_blank');
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a CSV or Excel file to upload.');
      return;
    }
    setError('');
    setResult(null);
    setLoading(true);

    try {
      const res = await api.uploadBulkFile(entityType, file);
      setResult(res);
      setFile(null);
    } catch (err) {
      setError(err.message || 'Bulk upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
          Bulk Data Migration & Import
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
          Seamless CSV and Excel batch ingestion for projects, historical reviews, and student progress logs.
        </p>
      </div>

      {error && (
        <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fb7185', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      {/* Select Entity Type */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '12px' }}>
          1. Select Entity Type to Ingest
        </label>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {[
            { id: 'projects', label: 'Projects & Cohorts' },
            { id: 'reviews', label: 'Faculty Reviews & Rubrics' },
            { id: 'progress', label: 'Weekly Progress Logs' }
          ].map(type => (
            <button
              key={type.id}
              onClick={() => {
                setEntityType(type.id);
                setResult(null);
              }}
              className={`btn ${entityType === type.id ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '10px 18px' }}
            >
              <FileSpreadsheet size={16} />
              <span>{type.label}</span>
            </button>
          ))}
        </div>

        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Download pre-formatted headers and sample data rows:
          </span>
          <button onClick={handleDownloadTemplate} className="btn btn-secondary" style={{ padding: '8px 14px' }}>
            <Download size={14} />
            <span>Download Sample {entityType.toUpperCase()} CSV</span>
          </button>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="glass-panel" style={{ padding: '32px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '16px' }}>
          2. Upload File (CSV / XLSX)
        </h2>
        
        <form onSubmit={handleUpload}>
          <div style={{
            border: '2px dashed rgba(99, 102, 241, 0.4)',
            borderRadius: '12px',
            padding: '36px 20px',
            textAlign: 'center',
            background: 'rgba(99, 102, 241, 0.03)',
            cursor: 'pointer',
            marginBottom: '20px'
          }}>
            <UploadCloud size={40} color="#818cf8" style={{ margin: '0 auto 12px' }} />
            <div style={{ fontWeight: 600, color: '#f8fafc', marginBottom: '4px' }}>
              {file ? file.name : `Drag and drop your ${entityType} file here`}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '16px' }}>
              Supports .csv, .xlsx, .xls formats with automatic column validation
            </div>
            <input
              type="file"
              accept=".csv, .xlsx, .xls"
              onChange={(e) => setFile(e.target.files[0])}
              style={{ display: 'none' }}
              id="bulk-file-input"
            />
            <label htmlFor="bulk-file-input" className="btn btn-secondary" style={{ cursor: 'pointer' }}>
              Choose File from Disk
            </label>
          </div>

          <button
            type="submit"
            disabled={!file || loading}
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px' }}
          >
            {loading ? 'Validating and Importing...' : `Import ${entityType.toUpperCase()} Now`}
          </button>
        </form>
      </div>

      {/* Result feedback */}
      {result && (
        <div className="glass-panel" style={{ padding: '24px', marginTop: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <CheckCircle size={22} color="#34d399" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#34d399' }}>
              Import Batch Processed Successfully
            </h3>
          </div>
          <div style={{ display: 'flex', gap: '20px', marginBottom: '16px' }}>
            <div style={{ fontSize: '0.9rem', color: '#cbd5e1' }}>
              Imported Rows: <b style={{ color: '#34d399' }}>{result.success_count}</b>
            </div>
            <div style={{ fontSize: '0.9rem', color: '#cbd5e1' }}>
              Invalid Rows: <b style={{ color: result.error_count > 0 ? '#fb7185' : '#34d399' }}>{result.error_count}</b>
            </div>
          </div>

          {result.errors && result.errors.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.9rem', color: '#fb7185', marginBottom: '8px' }}>Validation Rejections:</h4>
              <div style={{ maxHeight: '200px', overflowY: 'auto', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '12px', fontSize: '0.8rem', color: '#94a3b8' }}>
                {result.errors.map((err, idx) => (
                  <div key={idx} style={{ marginBottom: '6px' }}>
                    Row {err.row}: <span style={{ color: '#fb7185' }}>{err.error}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
