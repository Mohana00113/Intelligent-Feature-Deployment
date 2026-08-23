import { useState } from 'react'
import { evaluateFlag } from '../services/api'

const environments = [
  { value: 'development', label: 'Development' },
  { value: 'staging', label: 'Staging' },
  { value: 'production', label: 'Production' },
]

const sourceLabels = {
  user_targeting: 'User Targeting',
  group_targeting: 'Group Targeting',
  percentage_rollout: 'Percentage Rollout',
  environment_override: 'Environment Override',
  default: 'Default',
}

function EvaluationTestPanel({ flagKey, initialEnvironment = 'development' }) {
  const [userId, setUserId] = useState('')
  const [group, setGroup] = useState('')
  const [environment, setEnvironment] = useState(initialEnvironment)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [evaluating, setEvaluating] = useState(false)

  const handleEvaluate = async (event) => {
    event.preventDefault()
    if (!userId.trim()) {
      setError('User ID is required.')
      setResult(null)
      return
    }

    try {
      setEvaluating(true)
      setError('')
      const evaluation = await evaluateFlag({
        flag_key: flagKey,
        environment,
        user_id: userId.trim(),
        group: group.trim() || null,
      })
      setResult(evaluation)
    } catch (err) {
      setResult(null)
      setError(err.message || 'Unable to evaluate feature flag.')
    } finally {
      setEvaluating(false)
    }
  }

  return (
    <section style={styles.section} aria-labelledby="evaluation-test-title">
      <h3 id="evaluation-test-title" style={styles.title}>Evaluation Test</h3>
      <form onSubmit={handleEvaluate} style={styles.form}>
        <label style={styles.field}>
          <span style={styles.label}>User ID</span>
          <input value={userId} onChange={(event) => setUserId(event.target.value)} style={styles.input} placeholder="user123" />
        </label>
        <label style={styles.field}>
          <span style={styles.label}>Group</span>
          <input value={group} onChange={(event) => setGroup(event.target.value)} style={styles.input} placeholder="beta-users" />
        </label>
        <label style={styles.field}>
          <span style={styles.label}>Environment</span>
          <select value={environment} onChange={(event) => setEnvironment(event.target.value)} style={styles.input}>
            {environments.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <button type="submit" style={styles.button} disabled={evaluating}>
          {evaluating ? <><span style={styles.spinner} aria-label="Evaluating" /> Evaluating...</> : 'Evaluate'}
        </button>
      </form>

      {error ? <p role="alert" style={styles.error}>{error}</p> : null}
      {result ? (
        <div style={styles.result} aria-live="polite">
          <div style={styles.resultHeader}>
            <h4 style={styles.resultTitle}>Result</h4>
            <span style={result.cached ? styles.cachedStatus : styles.liveStatus}>
              <span aria-hidden="true">●</span> {result.cached ? 'Cached' : 'Live'}
            </span>
          </div>
          <Detail label="Value" value={String(result.value).toUpperCase()} />
          <Detail label="Source" value={sourceLabels[result.source] || result.source} />
          <Detail label="Environment" value={result.environment} />
        </div>
      ) : null}
    </section>
  )
}

function Detail({ label, value }) {
  return <div style={styles.detail}><strong>{label}</strong><span>{value}</span></div>
}

const styles = {
  section: { marginTop: '24px', padding: '20px', border: '1px solid #e2e8f0', borderRadius: '12px', background: '#ffffff' },
  title: { margin: '0 0 16px', color: '#111827', fontSize: '18px' },
  form: { display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '12px', alignItems: 'end' },
  field: { display: 'grid', gap: '6px' },
  label: { color: '#374151', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' },
  input: { width: '100%', boxSizing: 'border-box', border: '1px solid #d1d5db', borderRadius: '8px', padding: '10px 12px', fontSize: '14px', color: '#111827' },
  button: { border: 'none', borderRadius: '8px', padding: '10px 16px', background: '#2563eb', color: '#ffffff', cursor: 'pointer', fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '8px' },
  spinner: { width: '14px', height: '14px', border: '2px solid rgba(255, 255, 255, 0.45)', borderTopColor: '#ffffff', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite' },
  error: { margin: '14px 0 0', color: '#b91c1c', fontSize: '14px' },
  result: { marginTop: '18px', paddingTop: '16px', borderTop: '1px solid #e2e8f0' },
  resultHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '10px' },
  resultTitle: { margin: 0, color: '#111827', fontSize: '15px' },
  cachedStatus: { color: '#0369a1', fontSize: '12px', fontWeight: 700 },
  liveStatus: { color: '#15803d', fontSize: '12px', fontWeight: 700 },
  detail: { display: 'flex', justifyContent: 'space-between', gap: '16px', padding: '7px 0', color: '#475569', fontSize: '14px' },
}

export default EvaluationTestPanel