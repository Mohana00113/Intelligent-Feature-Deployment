import { createContext, useContext, useState } from 'react'

const EnvironmentContext = createContext(null)

export const EnvironmentProvider = ({ children }) => {
  const [environment, setEnvironment] = useState('development')

  return (
    <EnvironmentContext.Provider value={{ environment, setEnvironment }}>
      {children}
    </EnvironmentContext.Provider>
  )
}

export const useEnvironment = () => {
  const context = useContext(EnvironmentContext)

  if (!context) {
    throw new Error('useEnvironment must be used within an EnvironmentProvider')
  }

  return context
}

export default EnvironmentContext
