import { useCallback, useEffect, useMemo, useState } from 'react'
import { Route, Routes } from 'react-router-dom'

import Navbar from './components/Navbar'
import { EnvironmentProvider } from './context/EnvironmentContext'
import FeatureFlags from './pages/FeatureFlags'
import FlagDetail from './pages/FlagDetail'
import Environments from './pages/Environments'
import { getFlags } from './services/api'

const DashboardPage = () => {
  const [flags, setFlags] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadFlags = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const data = await getFlags()
      setFlags(Array.isArray(data) ? data : [])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load feature flag summary.'
      console.error('Dashboard summary fetch failed:', err)
      setError(message)
      setFlags([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    async function loadSummary() {
      try {
        if (!isMounted) {
          return
        }

        await loadFlags()
      } catch (loadError) {
        console.error('Dashboard summary failed to refresh:', loadError)
      }
    }

    void loadSummary()

    return () => {
      isMounted = false
    }
  }, [loadFlags])

  const summaryCards = useMemo(() => {
    const total = flags.length
    const enabled = flags.filter((flag) => flag.enabled).length
    const disabled = total - enabled

    return [
      { label: 'Total Feature Flags', value: total, accent: '#2563eb', soft: '#dbeafe' },
      { label: 'Enabled Feature Flags', value: enabled, accent: '#16a34a', soft: '#dcfce7' },
      { label: 'Disabled Feature Flags', value: disabled, accent: '#ef4444', soft: '#fee2e2' },
    ]
  }, [flags])

  return (
    <main style={styles.pageShell}>
      <div style={styles.dashboardShell}>
        <div style={styles.summaryGrid}>
          {summaryCards.map((card) => (
            <div key={card.label} style={{ ...styles.summaryCard, borderTop: `4px solid ${card.accent}` }}>
              <div style={{ ...styles.summaryBadge, background: card.soft, color: card.accent }}>
                {card.label}
              </div>
              <div style={styles.summaryValue}>{loading ? '—' : card.value}</div>
            </div>
          ))}
        </div>

        {error ? <p style={styles.errorMessage}>{error}</p> : null}

        <div style={styles.tableSection}>
          <FeatureFlags flags={flags} loading={loading} error={error} onRefresh={loadFlags} />
        </div>
      </div>
    </main>
  )
}

const AppContent = () => {
  return (
    <div>
      <Navbar />
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/flags" element={<FeatureFlags />} />
        <Route path="/flags/:key" element={<FlagDetail />} />
        <Route path="/environments" element={<Environments />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <EnvironmentProvider>
      <AppContent />
    </EnvironmentProvider>
  )
}

const styles = {
  pageShell: {
    background: 'linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)',
    minHeight: 'calc(100vh - 80px)',
    padding: '28px 20px 40px',
  },
  dashboardShell: {
    maxWidth: '1280px',
    margin: '0 auto',
    display: 'grid',
    gap: '24px',
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '18px',
  },
  summaryCard: {
    background: '#ffffff',
    borderRadius: '16px',
    padding: '20px 20px 18px',
    boxShadow: '0 10px 28px rgba(15, 23, 42, 0.08)',
    border: '1px solid #e2e8f0',
  },
  summaryBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    borderRadius: '999px',
    padding: '6px 10px',
    fontSize: '0.75rem',
    fontWeight: 700,
    letterSpacing: '0.02em',
    marginBottom: '16px',
  },
  summaryValue: {
    fontSize: '2rem',
    fontWeight: 800,
    color: '#0f172a',
    lineHeight: 1.1,
  },
  errorMessage: {
    color: '#b91c1c',
    background: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '10px',
    padding: '12px 14px',
    margin: 0,
  },
  tableSection: {
    background: 'transparent',
  },
}

export default App
