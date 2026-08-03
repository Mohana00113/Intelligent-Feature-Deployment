import { useEnvironment } from '../context/EnvironmentContext'

const Navbar = () => {
  const { environment, setEnvironment } = useEnvironment()

  return (
    <nav style={styles.navbar}>
      <div style={styles.brandWrap}>
        <strong style={styles.brand}>Intelligent Feature Deployment</strong>
      </div>

      <div style={styles.environmentWrap}>
        <label htmlFor="navbar-environment" style={styles.label}>Environment</label>
        <select
          id="navbar-environment"
          value={environment}
          onChange={(event) => setEnvironment(event.target.value)}
          style={styles.select}
        >
          <option value="development">Development</option>
          <option value="staging">Staging</option>
          <option value="production">Production</option>
        </select>
      </div>
    </nav>
  )
}

const styles = {
  navbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '16px',
    padding: '18px 28px',
    background: '#ffffff',
    borderBottom: '1px solid #e2e8f0',
    boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
  },
  brandWrap: {
    display: 'flex',
    alignItems: 'center',
  },
  brand: {
    fontSize: '1.35rem',
    fontWeight: 700,
    color: '#0f172a',
    letterSpacing: '-0.03em',
  },
  environmentWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    padding: '8px 12px',
  },
  label: {
    fontSize: '0.8rem',
    color: '#475569',
    fontWeight: 600,
  },
  select: {
    border: '1px solid #cbd5e1',
    borderRadius: '8px',
    background: '#ffffff',
    color: '#0f172a',
    padding: '8px 10px',
    fontSize: '0.92rem',
    outline: 'none',
  },
}

export default Navbar
