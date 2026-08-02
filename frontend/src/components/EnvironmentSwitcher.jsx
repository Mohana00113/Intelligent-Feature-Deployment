import { useEnvironment } from '../context/EnvironmentContext'

const EnvironmentSwitcher = () => {
  const { environment, setEnvironment } = useEnvironment()

  return (
    <div style={{ marginTop: '1rem' }}>
      <label htmlFor="environment">Environment:</label>
      <select
        id="environment"
        value={environment}
        onChange={(e) => setEnvironment(e.target.value)}
        style={{ marginLeft: '0.5rem' }}
      >
        <option value="development">Development</option>
        <option value="staging">Staging</option>
        <option value="production">Production</option>
      </select>
    </div>
  )
}

export default EnvironmentSwitcher
