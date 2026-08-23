import { useEffect, useState } from 'react'
import {
  getEnvironments,
  getFlagEnvironmentOverrides,
  getFlags,
  updateFlagEnvironmentOverride,
} from '../services/api'

const Environments = () => {
  const [environments, setEnvironments] = useState([])
  const [flags, setFlags] = useState([])
  const [selectedFlag, setSelectedFlag] = useState('')
  const [overrides, setOverrides] = useState([])
  const [drafts, setDrafts] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    async function loadCatalog() {
      try {
        setLoading(true)
        const [environmentData, flagData] = await Promise.all([getEnvironments(), getFlags()])
        setEnvironments(Array.isArray(environmentData) ? environmentData : [])
        const nextFlags = Array.isArray(flagData) ? flagData : []
        setFlags(nextFlags)
        setSelectedFlag(nextFlags[0]?.key || '')
      } catch (err) {
        setError(err.message || 'Unable to load environment configuration.')
      } finally {
        setLoading(false)
      }
    }

    void loadCatalog()
  }, [])

  useEffect(() => {
    if (!selectedFlag) {
      return
    }

    async function loadOverrides() {
      try {
        setError('')
        const data = await getFlagEnvironmentOverrides(selectedFlag)
        const nextOverrides = Array.isArray(data) ? data : []
        setOverrides(nextOverrides)
        setDrafts(Object.fromEntries(nextOverrides.map((item) => [item.environment_id, item])))
      } catch (err) {
        setError(err.message || 'Unable to load flag environment overrides.')
      }
    }

    void loadOverrides()
  }, [selectedFlag])

  const selectedFlagRecord = flags.find((flag) => flag.key === selectedFlag)

  const updateDraft = (environmentId, field, value) => {
    setDrafts((current) => ({
      ...current,
      [environmentId]: {
        ...current[environmentId],
        [field]: value,
      },
    }))
  }

  const saveOverride = async (environment) => {
    const draft = drafts[environment.id] || {}
    try {
      setSaving(environment.id)
      setError('')
      setNotice('')
      const saved = await updateFlagEnvironmentOverride(selectedFlag, environment.id, {
        enabled: Boolean(draft.enabled),
        rollout_percentage: Number(draft.rollout_percentage ?? 0),
      })
      setDrafts((current) => ({ ...current, [environment.id]: saved }))
      setOverrides((current) => current.map((item) => (item.environment_id === saved.environment_id ? saved : item)))
      setNotice(`${environment.name} saved.`)
    } catch (err) {
      setError(err.message || 'Unable to save environment override.')
    } finally {
      setSaving(null)
    }
  }

  return (
    <main style={styles.page}>
      <section style={styles.shell}>
        <div style={styles.header}>
          <div>
            <p style={styles.eyebrow}>Configuration</p>
            <h1 style={styles.title}>Environment Management</h1>
            <p style={styles.subtitle}>Tune each environment without changing the flag default.</p>
          </div>
          <label style={styles.selectorLabel} htmlFor="environment-flag-selector">
            Select Flag
            <select
              id="environment-flag-selector"
              value={selectedFlag}
              onChange={(event) => setSelectedFlag(event.target.value)}
              style={styles.select}
              disabled={loading || flags.length === 0}
            >
              {flags.length === 0 ? <option value="">No flags available</option> : null}
              {flags.map((flag) => <option key={flag.key} value={flag.key}>{flag.key}</option>)}
            </select>
          </label>
        </div>

        {error ? <p style={styles.error}>{error}</p> : null}
        {notice ? <p style={styles.notice}>{notice}</p> : null}

        <div style={styles.flagSummary}>
          <span style={styles.summaryLabel}>Selected flag</span>
          <strong>{selectedFlagRecord?.key || 'None'}</strong>
        </div>

        <div style={styles.table}>
          <div style={styles.tableHeader}>
            <span>Environment</span>
            <span>Enabled</span>
            <span>Rollout</span>
            <span>Action</span>
          </div>
          {loading ? <p style={styles.empty}>Loading environments...</p> : null}
          {!loading && environments.length === 0 ? <p style={styles.empty}>No environments configured.</p> : null}
          {environments.map((environment) => {
            const draft = drafts[environment.id] || overrides.find((item) => item.environment_id === environment.id) || {
              enabled: selectedFlagRecord?.enabled ?? false,
              rollout_percentage: selectedFlagRecord?.rollout_percentage ?? 0,
            }
            return (
              <div key={environment.id} style={styles.row}>
                <div>
                  <strong>{environment.name}</strong>
                  <small style={styles.key}>{environment.key}</small>
                </div>
                <label style={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={Boolean(draft.enabled)}
                    onChange={(event) => updateDraft(environment.id, 'enabled', event.target.checked)}
                  />
                  {draft.enabled ? 'ON' : 'OFF'}
                </label>
                <label style={styles.rolloutLabel}>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={draft.rollout_percentage ?? 0}
                    onChange={(event) => updateDraft(environment.id, 'rollout_percentage', event.target.value)}
                    style={styles.numberInput}
                  />
                  <span>%</span>
                </label>
                <button type="button" style={styles.saveButton} onClick={() => saveOverride(environment)} disabled={saving === environment.id}>
                  {saving === environment.id ? 'Saving...' : 'Save'}
                </button>
              </div>
            )
          })}
        </div>
      </section>
    </main>
  )
}

const styles = {
  page: { minHeight: 'calc(100vh - 80px)', background: 'linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)', padding: '32px 20px' },
  shell: { maxWidth: '1100px', margin: '0 auto', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '28px', boxShadow: '0 14px 32px rgba(15, 23, 42, 0.08)' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'end', gap: '24px', flexWrap: 'wrap', marginBottom: '24px' },
  eyebrow: { margin: 0, color: '#2563eb', fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.12em' },
  title: { margin: '6px 0', color: '#0f172a', fontSize: '30px' },
  subtitle: { margin: 0, color: '#64748b' },
  selectorLabel: { display: 'grid', gap: '6px', minWidth: '240px', color: '#334155', fontWeight: 700, fontSize: '13px' },
  select: { padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: '8px', background: '#fff', color: '#0f172a' },
  error: { padding: '12px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#b91c1c' },
  notice: { padding: '12px 14px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', color: '#166534' },
  flagSummary: { display: 'flex', gap: '10px', alignItems: 'baseline', padding: '14px 16px', marginBottom: '18px', background: '#eff6ff', borderRadius: '10px', color: '#1e3a8a' },
  summaryLabel: { fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700 },
  table: { border: '1px solid #e2e8f0', borderRadius: '10px', overflow: 'hidden' },
  tableHeader: { display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 110px', gap: '16px', padding: '12px 16px', background: '#f8fafc', color: '#64748b', fontSize: '12px', fontWeight: 800, textTransform: 'uppercase' },
  row: { display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 110px', gap: '16px', alignItems: 'center', padding: '16px', borderTop: '1px solid #e2e8f0', color: '#0f172a' },
  key: { display: 'block', marginTop: '4px', color: '#94a3b8' },
  checkboxLabel: { display: 'flex', alignItems: 'center', gap: '8px', color: '#334155', fontWeight: 700 },
  rolloutLabel: { display: 'flex', alignItems: 'center', gap: '6px' },
  numberInput: { width: '72px', padding: '8px', border: '1px solid #cbd5e1', borderRadius: '6px' },
  saveButton: { border: 0, borderRadius: '7px', padding: '9px 12px', background: '#2563eb', color: '#fff', fontWeight: 700, cursor: 'pointer' },
  empty: { padding: '20px 16px', color: '#64748b' },
}

export default Environments
