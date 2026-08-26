import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useEnvironment } from '../context/EnvironmentContext'
import { deleteFlag, getEvaluationMetrics, getFlagByKey, updateFlag } from '../services/api'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import EnvironmentOverridePanel from '../components/EnvironmentOverridePanel'
import EvaluationTestPanel from '../components/EvaluationTestPanel'
import TargetingRulePanel from '../components/TargetingRulePanel'

const environmentLabels = {
  1: 'Development',
  2: 'Staging',
  3: 'Production',
}

function FlagDetail() {
  const { key } = useParams()
  const navigate = useNavigate()
  const { environment } = useEnvironment()
  const [flag, setFlag] = useState(null)
  const [, setTargetUsers] = useState([])
  const [, setTargetGroups] = useState([])
  const [rolloutPercentage, setRolloutPercentage] = useState(0)
  const [savingRollout, setSavingRollout] = useState(false)
  const [savingTargeting, setSavingTargeting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [metricDays, setMetricDays] = useState(7)
  const [metrics, setMetrics] = useState([])
  const [metricsLoading, setMetricsLoading] = useState(true)
  const [metricsError, setMetricsError] = useState('')

  const handleDelete = async () => {
    if (!flag || !key) {
      return
    }

    const confirmed = window.confirm(`Delete feature flag '${key}'? This action cannot be undone.`)
    if (!confirmed) {
      return
    }

    try {
      await deleteFlag(key)
      navigate('/flags')
    } catch (err) {
      setError(err.message || 'Unable to delete feature flag.')
    }
  }

  useEffect(() => {
    async function loadFlag() {
      try {
        setLoading(true)
        setError('')
        const data = await getFlagByKey(key)
        setFlag(data)
        setRolloutPercentage(Number(data?.rollout_percentage ?? 0))
      } catch (err) {
        setError(err.message || 'Unable to load feature flag.')
      } finally {
        setLoading(false)
      }
    }

    loadFlag()
  }, [key])

  useEffect(() => {
    async function loadMetrics() {
      try {
        setMetricsLoading(true)
        setMetricsError('')
        const data = await getEvaluationMetrics(key, environment, metricDays)
        setMetrics(Array.isArray(data?.points) ? data.points : [])
      } catch (err) {
        setMetricsError(err.message || 'Unable to load evaluation metrics.')
        setMetrics([])
      } finally {
        setMetricsLoading(false)
      }
    }

    if (key) {
      void loadMetrics()
    }
  }, [key, environment, metricDays])

  const handleRolloutSave = async (nextPercentage) => {
    if (!flag || !key) {
      return
    }

    const value = Number.isFinite(nextPercentage) ? Number(nextPercentage) : 0
    try {
      setSavingRollout(true)
      setError('')
      await updateFlag(flag.key, { rollout_percentage: value })
      const updated = await getFlagByKey(key)
      setFlag(updated)
      setRolloutPercentage(Number(updated?.rollout_percentage ?? value))
    } catch (err) {
      setRolloutPercentage(Number(flag.rollout_percentage ?? 0))
      setError(err.message || 'Unable to save rollout percentage.')
    } finally {
      setSavingRollout(false)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.headerRow}>
          <button type="button" style={styles.backButton} onClick={() => navigate('/flags')}>
            ← Back to flags
          </button>
          <button type="button" style={styles.deleteButton} onClick={handleDelete}>
            Delete Flag
          </button>
        </div>
        <h2 style={styles.title}>Feature Flag Details</h2>

        {loading ? (
          <p style={styles.loadingMessage}><span style={styles.spinner} aria-label="Loading" /> Loading flag details...</p>
        ) : error ? (
          <p style={styles.error}>{error}</p>
        ) : flag ? (
          <>
            <div style={styles.detailsGrid}>
              <DetailRow label="Flag Key" value={flag.key} />
              <DetailRow label="Type" value={flag.type} />
              <DetailRow label="Default Value" value={String(flag.default_value)} />
              <DetailRow label="Description" value={flag.description || 'No description provided.'} />
              <DetailRow label="Current Status" value={flag.enabled ? 'Enabled' : 'Disabled'} />
              <DetailRow label="Rollout Percentage" value={`${Number(flag.rollout_percentage ?? 0)}%`} />
              <DetailRow label="Owner Team" value={flag.owner_team} />
              <DetailRow label="Environment" value={environmentLabels[flag.environment_id] || String(flag.environment_id)} />
              <DetailRow label="Record ID" value={String(flag.id)} />
            </div>

            <div style={styles.rolloutSection}>
              <h3 style={styles.targetingRulesTitle}>Percentage Rollout</h3>
              <label htmlFor="rollout-slider" style={styles.sliderLabel}>Rollout percentage</label>
              <div style={styles.sliderRow}>
                <input
                  id="rollout-slider"
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={rolloutPercentage}
                  onChange={(event) => setRolloutPercentage(Number(event.target.value))}
                  onMouseUp={() => handleRolloutSave(rolloutPercentage)}
                  onTouchEnd={() => handleRolloutSave(rolloutPercentage)}
                  style={styles.sliderInput}
                  aria-label="Percentage rollout"
                />
                <span style={styles.sliderValue}>{rolloutPercentage}%</span>
              </div>
              <div style={styles.sliderMeta}>
                <span>{savingRollout ? <><span style={styles.inlineSpinner} aria-label="Saving" /> Saving...</> : `Enabled for ${rolloutPercentage}% of users.`}</span>
              </div>
            </div>

            <div style={styles.targetingRulesSection}>
              <h3 style={styles.targetingRulesTitle}>Targeting Rules</h3>
              <TargetingRulePanel
                users={flag.target_users || []}
                groups={flag.target_groups || []}
                onChange={(users, groups) => {
                  setTargetUsers(users)
                  setTargetGroups(groups)
                }}
                onSave={async (users, groups) => {
                  try {
                    setSavingTargeting(true)
                    await updateFlag(flag.key, { target_users: users, target_groups: groups })
                    const updated = await getFlagByKey(key)
                    setFlag(updated)
                    setTargetUsers([])
                    setTargetGroups([])
                  } catch (err) {
                    setError(err.message || 'Unable to save targeting rules.')
                  } finally {
                    setSavingTargeting(false)
                  }
                }}
                saving={savingTargeting}
              />
            </div>

            <EnvironmentOverridePanel flag={flag} />

            <EvaluationMetricsPanel
              days={metricDays}
              metrics={metrics}
              loading={metricsLoading}
              error={metricsError}
              onDaysChange={setMetricDays}
            />

            <EvaluationTestPanel
              flagKey={flag.key}
              initialEnvironment={environment}
            />
          </>
        ) : (
          <p style={styles.message}>No flag data available.</p>
        )}
      </div>
    </div>
  )
}

function EvaluationMetricsPanel({ days, metrics, loading, error, onDaysChange }) {
  const chartData = metrics.map((point) => ({
    ...point,
    label: new Date(point.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' }),
  }))

  return (
    <section style={styles.metricsSection} aria-labelledby="evaluation-metrics-title">
      <div style={styles.metricsHeader}>
        <div>
          <h3 id="evaluation-metrics-title" style={styles.targetingRulesTitle}>Evaluation Count</h3>
          <p style={styles.metricsHint}>Hourly evaluations recorded after the daily metrics flush.</p>
        </div>
        <label style={styles.metricsSelectLabel}>
          Range
          <select value={days} onChange={(event) => onDaysChange(Number(event.target.value))} style={styles.metricsSelect}>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </label>
      </div>
      {loading ? <p style={styles.metricsStatus}>Loading evaluation metrics...</p> : null}
      {error ? <p style={styles.error}>{error}</p> : null}
      {!loading && !error && chartData.length === 0 ? <p style={styles.metricsStatus}>No evaluation metrics available yet.</p> : null}
      {!loading && !error && chartData.length > 0 ? (
        <div style={styles.chart}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 12, right: 18, left: 0, bottom: 4 }}>
              <XAxis dataKey="label" minTickGap={28} tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} width={36} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(value) => [value, 'Evaluations']} />
              <Line type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </section>
  )
}

function DetailRow({ label, value }) {
  return (
    <div style={styles.detailRow}>
      <strong style={styles.detailLabel}>{label}</strong>
      <span style={styles.detailValue}>{value}</span>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    background: '#f8fafc',
    padding: '24px',
    fontFamily: 'Arial, sans-serif',
  },
  card: {
    maxWidth: '860px',
    margin: '0 auto',
    background: '#ffffff',
    borderRadius: '14px',
    boxShadow: '0 14px 36px rgba(15, 23, 42, 0.1)',
    padding: '28px',
  },
  headerRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '18px',
    gap: '12px',
  },
  backButton: {
    border: 'none',
    background: 'transparent',
    color: '#2563eb',
    cursor: 'pointer',
    fontSize: '14px',
  },
  deleteButton: {
    border: 'none',
    background: '#fee2e2',
    color: '#991b1b',
    borderRadius: '8px',
    padding: '8px 12px',
    cursor: 'pointer',
    fontWeight: 600,
  },
  title: {
    margin: '0 0 16px',
    color: '#111827',
  },
  message: {
    color: '#6b7280',
  },
  loadingMessage: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: '#6b7280',
  },
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid #dbeafe',
    borderTopColor: '#2563eb',
    borderRadius: '50%',
    display: 'inline-block',
    animation: 'spin 0.8s linear infinite',
  },
  inlineSpinner: {
    width: '12px',
    height: '12px',
    marginRight: '6px',
    border: '2px solid #dbeafe',
    borderTopColor: '#2563eb',
    borderRadius: '50%',
    display: 'inline-block',
    animation: 'spin 0.8s linear infinite',
    verticalAlign: 'middle',
  },
  error: {
    color: '#b91c1c',
  },
  detailsGrid: {
    display: 'grid',
    gap: '16px',
    gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
  },
  detailRow: {
    padding: '18px',
    borderRadius: '12px',
    background: '#f8fafc',
  },
  detailLabel: {
    display: 'block',
    marginBottom: '8px',
    color: '#374151',
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  },
  detailValue: {
    color: '#111827',
    fontSize: '16px',
  },
  rolloutSection: {
    marginTop: '24px',
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '20px',
    display: 'grid',
    gap: '12px',
  },
  sliderLabel: {
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: '#374151',
    fontWeight: 700,
  },
  sliderRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  sliderInput: {
    flex: 1,
    accentColor: '#2563eb',
  },
  sliderValue: {
    minWidth: '52px',
    textAlign: 'right',
    fontWeight: 700,
    color: '#111827',
  },
  sliderMeta: {
    color: '#475569',
    fontSize: '14px',
  },
  targetingRulesSection: {
    marginTop: '24px',
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '20px',
  },
  metricsSection: { marginTop: '24px', padding: '20px', border: '1px solid #e2e8f0', borderRadius: '12px', background: '#ffffff' },
  metricsHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '16px', flexWrap: 'wrap' },
  metricsHint: { margin: '6px 0 0', color: '#64748b', fontSize: '13px' },
  metricsSelectLabel: { display: 'grid', gap: '6px', color: '#64748b', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase' },
  metricsSelect: { border: '1px solid #cbd5e1', borderRadius: '8px', padding: '9px 10px', color: '#0f172a', background: '#fff', fontSize: '14px' },
  metricsStatus: { color: '#64748b', fontSize: '14px', padding: '20px 0', margin: 0 },
  chart: { width: '100%', height: '260px', marginTop: '14px' },
  targetingRulesTitle: {
    margin: '0 0 8px',
    color: '#111827',
    fontSize: '18px',
  },
  targetingRulesText: {
    margin: 0,
    color: '#475569',
    fontSize: '14px',
  },
}

export default FlagDetail
