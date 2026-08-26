import { useCallback, useEffect, useState } from 'react';

import { getAuditLogs } from '../services/api';
import { useEnvironment } from '../context/EnvironmentContext';

const emptyFilters = { actor: '', flag_key: '', from_date: '', to_date: '' };

function AuditLogs() {
  const [filters, setFilters] = useState(emptyFilters);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);
  const { environment } = useEnvironment();

  const loadLogs = useCallback(async (nextFilters) => {
    try {
      setLoading(true);
      setError('');
      const data = await getAuditLogs({ ...nextFilters, environment });
      setLogs(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load audit logs.');
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [environment]);

  useEffect(() => {
    const task = window.setTimeout(() => void loadLogs(emptyFilters), 0);
    return () => window.clearTimeout(task);
  }, [loadLogs]);

  const handleFilterChange = (event) => {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    void loadLogs(filters);
  };

  const clearFilters = () => {
    setFilters(emptyFilters);
    void loadLogs(emptyFilters);
  };

  return (
    <main style={styles.page}>
      <section style={styles.shell}>
        <div style={styles.headingRow}>
          <div>
            <p style={styles.eyebrow}>Change history</p>
            <h1 style={styles.title}>Audit Logs</h1>
          </div>
          <button type="button" style={styles.secondaryButton} onClick={() => void loadLogs(filters)} disabled={loading}>Refresh</button>
        </div>

        <form style={styles.filters} onSubmit={handleSubmit}>
          <label style={styles.field}>Actor<input name="actor" value={filters.actor} onChange={handleFilterChange} placeholder="Filter actor" /></label>
          <label style={styles.field}>Flag key<input name="flag_key" value={filters.flag_key} onChange={handleFilterChange} placeholder="Filter flag" /></label>
          <label style={styles.field}>From<input type="date" name="from_date" value={filters.from_date} onChange={handleFilterChange} /></label>
          <label style={styles.field}>To<input type="date" name="to_date" value={filters.to_date} onChange={handleFilterChange} /></label>
          <button type="submit" style={styles.primaryButton}>Apply filters</button>
          <button type="button" style={styles.linkButton} onClick={clearFilters}>Clear</button>
        </form>

        {loading ? <p style={styles.status}>Loading audit history...</p> : null}
        {error ? <p style={styles.error}>{error}</p> : null}
        {!loading && !error && logs.length === 0 ? <p style={styles.status}>No audit events match these filters.</p> : null}
        {!loading && !error && logs.length > 0 ? (
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead><tr>{['Timestamp', 'Actor', 'Flag', 'Action Type', 'View Diff'].map((heading) => <th key={heading} style={styles.th}>{heading}</th>)}</tr></thead>
              <tbody>{logs.map((log) => (
                <tr key={log.id}>
                  <td style={styles.td}>{new Date(log.timestamp).toLocaleString()}</td>
                  <td style={styles.td}>{log.actor}</td>
                  <td style={styles.td}>{log.flag_key}</td>
                  <td style={styles.td}><span style={styles.action}>{log.action}</span></td>
                  <td style={styles.td}><button type="button" style={styles.viewButton} onClick={() => setSelectedLog(log)}>View Diff</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : null}
      </section>
      {selectedLog ? <AuditDetail log={selectedLog} onClose={() => setSelectedLog(null)} /> : null}
    </main>
  );
}

function AuditDetail({ log, onClose }) {
  return (
    <div style={styles.overlay} role="presentation" onClick={onClose}>
      <section style={styles.modal} role="dialog" aria-modal="true" aria-labelledby="audit-detail-title" onClick={(event) => event.stopPropagation()}>
        <div style={styles.modalHeader}><h2 id="audit-detail-title" style={styles.modalTitle}>Audit Event</h2><button type="button" style={styles.closeButton} onClick={onClose} aria-label="Close">×</button></div>
        <div style={styles.detailGrid}>
          <Detail label="Timestamp" value={new Date(log.timestamp).toLocaleString()} />
          <Detail label="Actor" value={log.actor} />
          <Detail label="Environment" value={log.environment || 'All'} />
          <Detail label="Flag" value={log.flag_key} />
          <Detail label="Action" value={log.action} />
        </div>
        <JsonBlock label="Previous state" value={log.previous_state} />
        <JsonBlock label="New state" value={log.new_state} />
        <JsonBlock label="JSON diff" value={log.diff} />
      </section>
    </div>
  );
}

function Detail({ label, value }) { return <div><strong style={styles.detailLabel}>{label}</strong><div>{value}</div></div>; }
function JsonBlock({ label, value }) { return <div style={styles.jsonSection}><strong style={styles.detailLabel}>{label}</strong><pre style={styles.json}>{JSON.stringify(value, null, 2)}</pre></div>; }

const styles = {
  page: { minHeight: 'calc(100vh - 80px)', background: 'linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)', padding: '28px 20px 48px' },
  shell: { maxWidth: '1280px', margin: '0 auto', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 10px 28px rgba(15, 23, 42, .07)', padding: '24px' },
  headingRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', marginBottom: '22px' },
  eyebrow: { margin: 0, color: '#64748b', fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em' },
  title: { margin: '4px 0 0', color: '#0f172a', fontSize: '1.8rem' },
  filters: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', alignItems: 'end', marginBottom: '22px', paddingBottom: '20px', borderBottom: '1px solid #e2e8f0' },
  field: { display: 'grid', gap: '6px', color: '#475569', fontSize: '0.8rem', fontWeight: 700 },
  input: {},
  primaryButton: { border: 0, borderRadius: '8px', background: '#2563eb', color: '#fff', padding: '10px 14px', fontWeight: 700, cursor: 'pointer' },
  secondaryButton: { border: '1px solid #cbd5e1', borderRadius: '8px', background: '#fff', color: '#1e293b', padding: '9px 14px', fontWeight: 700, cursor: 'pointer' },
  linkButton: { border: 0, background: 'transparent', color: '#2563eb', padding: '10px 4px', fontWeight: 700, cursor: 'pointer' },
  status: { color: '#64748b', padding: '30px 0', textAlign: 'center' },
  error: { color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '12px' },
  tableWrap: { overflowX: 'auto' }, table: { width: '100%', borderCollapse: 'collapse', minWidth: '680px' },
  th: { textAlign: 'left', color: '#475569', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '12px', borderBottom: '2px solid #e2e8f0' },
  td: { padding: '14px 12px', color: '#1e293b', borderBottom: '1px solid #e2e8f0', fontSize: '0.9rem' }, action: { display: 'inline-block', color: '#075985', background: '#e0f2fe', borderRadius: '999px', padding: '4px 8px', fontSize: '0.75rem', fontWeight: 800 },
  viewButton: { border: 0, background: 'transparent', color: '#2563eb', fontWeight: 700, cursor: 'pointer' },
  overlay: { position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, .46)', display: 'grid', placeItems: 'center', padding: '20px', zIndex: 10 },
  modal: { background: '#fff', borderRadius: '12px', width: 'min(720px, 100%)', maxHeight: '90vh', overflowY: 'auto', padding: '24px', boxShadow: '0 20px 50px rgba(15, 23, 42, .25)' },
  modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }, modalTitle: { margin: 0, color: '#0f172a' }, closeButton: { border: 0, background: 'transparent', fontSize: '1.7rem', color: '#64748b', cursor: 'pointer' },
  detailGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '18px', color: '#1e293b' }, detailLabel: { display: 'block', color: '#64748b', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '5px' }, jsonSection: { marginTop: '16px' }, json: { margin: '6px 0 0', padding: '14px', background: '#0f172a', color: '#dbeafe', borderRadius: '8px', overflowX: 'auto', fontSize: '0.8rem' },
};

export default AuditLogs;