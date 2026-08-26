import { useCallback, useEffect, useState } from 'react';

import { getCleanupSuggestions, markCleanupReviewed } from '../services/api';

function CleanupSuggestions() {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reviewing, setReviewing] = useState('');

  const loadSuggestions = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getCleanupSuggestions();
      setSuggestions(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load cleanup suggestions.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const task = window.setTimeout(() => void loadSuggestions(), 0);
    return () => window.clearTimeout(task);
  }, [loadSuggestions]);

  const review = async (flagKey) => {
    try {
      setReviewing(flagKey);
      await markCleanupReviewed(flagKey);
      await loadSuggestions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to mark suggestion reviewed.');
    } finally {
      setReviewing('');
    }
  };

  return (
    <section style={styles.section} aria-labelledby="cleanup-suggestions-title">
      <div style={styles.header}>
        <div>
          <p style={styles.eyebrow}>Lifecycle hygiene</p>
          <h2 id="cleanup-suggestions-title" style={styles.title}>Cleanup Suggestions</h2>
        </div>
        <button type="button" style={styles.refresh} onClick={() => void loadSuggestions()} disabled={loading}>Refresh</button>
      </div>
      {loading ? <p style={styles.status}>Scanning flag history...</p> : null}
      {error ? <p style={styles.error}>{error}</p> : null}
      {!loading && !error && suggestions.length === 0 ? <p style={styles.status}>No stale flags need review.</p> : null}
      {!loading && suggestions.length > 0 ? (
        <div style={styles.list}>
          {suggestions.map((suggestion) => (
            <div key={suggestion.flag_key} style={styles.item}>
              <div>
                <strong style={styles.flag}>{suggestion.flag_key}</strong>
                <p style={styles.detail}>{suggestion.state === 'fully_rolled_out' ? 'Fully rolled out' : 'Fully disabled'} for {suggestion.stale_days} days</p>
                <p style={styles.date}>Since {new Date(suggestion.stale_since).toLocaleDateString()}</p>
              </div>
              {suggestion.reviewed ? <span style={styles.reviewed}>Reviewed</span> : <button type="button" style={styles.reviewButton} onClick={() => void review(suggestion.flag_key)} disabled={reviewing === suggestion.flag_key}>{reviewing === suggestion.flag_key ? 'Saving...' : 'Mark reviewed'}</button>}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

const styles = {
  section: { background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '22px', boxShadow: '0 10px 28px rgba(15, 23, 42, 0.06)' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '16px', marginBottom: '14px' },
  eyebrow: { margin: 0, color: '#b45309', fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase' },
  title: { margin: '4px 0 0', color: '#0f172a', fontSize: '1.3rem' },
  refresh: { border: '1px solid #cbd5e1', borderRadius: '8px', padding: '8px 12px', background: '#fff', color: '#334155', fontWeight: 700, cursor: 'pointer' },
  status: { margin: 0, color: '#64748b', padding: '18px 0' },
  error: { margin: 0, padding: '10px', color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px' },
  list: { display: 'grid', gap: '10px' },
  item: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', padding: '14px', border: '1px solid #fde68a', borderLeft: '4px solid #f59e0b', borderRadius: '8px', background: '#fffbeb' },
  flag: { color: '#0f172a' }, detail: { margin: '5px 0 0', color: '#475569', fontSize: '0.9rem' }, date: { margin: '3px 0 0', color: '#94a3b8', fontSize: '0.78rem' },
  reviewButton: { border: 0, borderRadius: '8px', padding: '9px 12px', background: '#0f766e', color: '#fff', fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' },
  reviewed: { color: '#166534', fontWeight: 800, fontSize: '0.82rem', whiteSpace: 'nowrap' },
};

export default CleanupSuggestions;