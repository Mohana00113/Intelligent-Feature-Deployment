import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { deleteFlag, getFlagByKey, updateFlag } from '../services/api'
import TargetingRulePanel from '../components/TargetingRulePanel'

const environmentLabels = {
  1: 'Development',
  2: 'Staging',
  3: 'Production',
}

function FlagDetail() {
  const { key } = useParams()
  const navigate = useNavigate()
  const [flag, setFlag] = useState(null)
  const [targetUsers, setTargetUsers] = useState([])
  const [targetGroups, setTargetGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
      } catch (err) {
        setError(err.message || 'Unable to load feature flag.')
      } finally {
        setLoading(false)
      }
    }

    loadFlag()
  }, [key])

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
          <p style={styles.message}>Loading flag details...</p>
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
              <DetailRow label="Owner Team" value={flag.owner_team} />
              <DetailRow label="Environment" value={environmentLabels[flag.environment_id] || String(flag.environment_id)} />
              <DetailRow label="Record ID" value={String(flag.id)} />
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
                    await updateFlag(flag.key, { target_users: users, target_groups: groups })
                    const updated = await getFlagByKey(key)
                    setFlag(updated)
                    setTargetUsers([])
                    setTargetGroups([])
                  } catch (err) {
                    setError(err.message || 'Unable to save targeting rules.')
                  }
                }}
              />
            </div>
          </>
        ) : (
          <p style={styles.message}>No flag data available.</p>
        )}
      </div>
    </div>
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
  targetingRulesSection: {
    marginTop: '24px',
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    padding: '20px',
  },
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
