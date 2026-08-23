import { useEffect, useState } from 'react'
import { getFlagEnvironmentOverrides, updateFlagEnvironmentOverride } from '../services/api'

const environments = [
  { id: 1, key: 'development', label: 'Development' },
  { id: 2, key: 'staging', label: 'Staging' },
  { id: 3, key: 'production', label: 'Production' },
]

function createDraft(flag, override) {
  return override ? {
    enabled: Boolean(override.enabled),
    default_value: Boolean(override.default_value),
    rollout_percentage: Number(override.rollout_percentage ?? 0),
  } : {
    enabled: Boolean(flag.enabled),
    default_value: Boolean(flag.default_value),
    rollout_percentage: Number(flag.rollout_percentage ?? 0),
  }
}

function EnvironmentOverridePanel({ flag }) {
  const [selectedEnvironment, setSelectedEnvironment] = useState(flag.environment_id || 1)
  const [overrides, setOverrides] = useState([])
  const [draft, setDraft] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    async function loadOverrides() {
      try {
        setLoading(true)
        setError('')
        const data = await getFlagEnvironmentOverrides(flag.key)
        const nextOverrides = Array.isArray(data) ? data : []
        setOverrides(nextOverrides)
        setDraft(createDraft(flag, nextOverrides.find((item) => item.environment_id === selectedEnvironment)))
      } catch (err) {
        setError(err.message || 'Unable to load environment overrides.')
      } finally {
        setLoading(false)
      }
    }

    void loadOverrides()
  }, [flag, selectedEnvironment])

  const selectedLabel = environments.find((environment) => environment.id === selectedEnvironment)?.label || 'selected environment'

  const handleSave = async () => {
    if (!draft) {
      return
    }

    try {
      setSaving(true)
      setError('')
      setNotice('')
      const saved = await updateFlagEnvironmentOverride(flag.key, selectedEnvironment, draft)
      setOverrides((current) => [
        ...current.filter((item) => item.environment_id !== selectedEnvironment),
        saved,
      ])
      setNotice(`${selectedLabel} override saved. Evaluation cache invalidated.`)
    } catch (err) {
      setError(err.message || 'Unable to save environment override.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section style={styles.section} aria-labelledby="environment-override-title">
      <h3 id="environment-override-title" style={styles.title}>Environment Override</h3>
      <p style={styles.hint}>Set a value and rollout for one environment without changing the default flag configuration.</p>
      <label style={styles.field}>
        <span style={styles.label}>Environment</span>
        <select
          value={selectedEnvironment}
          onChange={(event) => {
            const nextEnvironment = Number(event.target.value)
            setSelectedEnvironment(nextEnvironment)
            setDraft(createDraft(flag, overrides.find((item) => item.environment_id === nextEnvironment)))
            setNotice('')
          }}
          style={styles.input}
        >
          {environments.map((environment) => <option key={environment.id} value={environment.id}>{environment.label}</option>)}
        </select>
      </label>
      {loading ? <p style={styles.status}>Loading override...</p> : draft ? (
        <>
          <div style={styles.grid}>
            <label style={styles.field}>
              <span style={styles.label}>Override Value</span>
              <select
                value={String(draft.default_value)}
                onChange={(event) => setDraft((current) => ({ ...current, default_value: event.target.value === 'true' }))}
                style={styles.input}
              >
                <option value="true">True</option>
                <option value="false">False</option>
              </select>
            </label>
            <label style={styles.field}>
              <span style={styles.label}>Percentage Rollout</span>
              <input
                type="number"
                min="0"
                max="100"
                value={draft.rollout_percentage}
                onChange={(event) => setDraft((current) => ({ ...current, rollout_percentage: Number(event.target.value) }))}
                style={styles.input}
              />
            </label>
          </div>
          <label style={styles.checkbox}>
            <input
              type="checkbox"
              checked={draft.enabled}
              onChange={(event) => setDraft((current) => ({ ...current, enabled: event.target.checked }))}
            />
            Enabled in {selectedLabel}
          </label>
          <button type="button" onClick={handleSave} disabled={saving} style={styles.button}>
            {saving ? 'Saving...' : 'Save Environment Override'}
          </button>
        </>
      ) : null}
      {error ? <p role="alert" style={styles.error}>{error}</p> : null}
      {notice ? <p role="status" style={styles.notice}>{notice}</p> : null}
    </section>
  )
}

const styles = {
  section: { marginTop: '24px', padding: '20px', border: '1px solid #e2e8f0', borderRadius: '12px', background: '#ffffff' },
  title: { margin: '0 0 8px', color: '#111827', fontSize: '18px' },
  hint: { margin: '0 0 16px', color: '#6b7280', fontSize: '13px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '12px', marginTop: '12px' },
  field: { display: 'grid', gap: '6px' },
  label: { color: '#374151', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' },
  input: { width: '100%', boxSizing: 'border-box', border: '1px solid #d1d5db', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', color: '#111827' },
  checkbox: { display: 'flex', alignItems: 'center', gap: '8px', marginTop: '14px', color: '#374151', fontSize: '14px' },
  button: { marginTop: '16px', border: 'none', borderRadius: '8px', padding: '10px 16px', background: '#2563eb', color: '#ffffff', cursor: 'pointer', fontWeight: 600 },
  status: { color: '#6b7280', fontSize: '14px' },
  error: { margin: '14px 0 0', color: '#b91c1c', fontSize: '14px' },
  notice: { margin: '14px 0 0', color: '#166534', fontSize: '14px' },
}

export default EnvironmentOverridePanel
