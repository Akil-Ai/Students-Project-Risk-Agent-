import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  FileText,
  Download,
  FileSpreadsheet,
  Printer,
  RefreshCw,
  Search
} from 'lucide-react';

export default function Reports() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  const loadReports = async () => {
    setLoading(true);
    try {
      const res = await api.getReportsSummary();
      setData(res);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to generate reports preview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleDownloadCsv = () => {
    if (data.length === 0) return;
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map(row =>
      Object.values(row)
        .map(val => `"${String(val).replace(/"/g, '""')}"`)
        .join(',')
    );
    const csvContent = [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `risk_assessment_report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadPdf = () => {
    const token = api.getToken();
    fetch(`${api.getBaseUrl()}/reports/pdf`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => res.blob())
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'project_risk_report.pdf');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      })
      .catch(err => alert(`PDF generation error: ${err.message}`));
  };

  const filtered = data.filter(d =>
    d.project_title.toLowerCase().includes(search.toLowerCase()) ||
    d.guide.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Export Risk & Compliance Reports
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
            One-click audit export of institutional risk assessment summaries as CSV or printable PDF documents.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleDownloadCsv} className="btn btn-secondary">
            <FileSpreadsheet size={16} />
            <span>Export CSV</span>
          </button>
          <button onClick={handleDownloadPdf} className="btn btn-primary">
            <Printer size={16} />
            <span>Generate PDF Report</span>
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fb7185', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      {/* Filter and Preview Container */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
            Report Data Preview ({filtered.length} Projects)
          </h2>
          <div style={{ position: 'relative', width: '260px' }}>
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '11px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="Search report..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '32px', padding: '7px 10px 7px 32px', fontSize: '0.82rem' }}
            />
          </div>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '40px', color: '#94a3b8' }}>
            <RefreshCw size={28} style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        ) : (
          <div className="data-table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Project Title</th>
                  <th>Type</th>
                  <th>Semester</th>
                  <th>Faculty Guide</th>
                  <th>Risk Bucket</th>
                  <th>Delay Probability</th>
                  <th>Primary Driver</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(row => (
                  <tr key={row.project_id}>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', color: '#818cf8', fontWeight: 600 }}>
                      #{row.project_id}
                    </td>
                    <td style={{ fontWeight: 600, color: '#f8fafc' }}>{row.project_title}</td>
                    <td>{row.type}</td>
                    <td>{row.semester}</td>
                    <td>{row.guide}</td>
                    <td>
                      <span className={`badge ${row.risk_bucket === 'High' ? 'badge-high' : row.risk_bucket === 'Medium' ? 'badge-medium' : 'badge-low'}`}>
                        {row.risk_bucket}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>
                      {row.delay_probability}
                    </td>
                    <td style={{ color: '#94a3b8', fontSize: '0.84rem' }}>{row.primary_driver}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
