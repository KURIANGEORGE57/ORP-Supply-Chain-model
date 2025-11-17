import { useState } from 'react'
import AssertionForm from './pages/AssertionForm'
import EvaluationPanel from './pages/EvaluationPanel'
import BatchView from './pages/BatchView'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

function App() {
  const [activeTab, setActiveTab] = useState('assertion')
  const [currentAgent, setCurrentAgent] = useState({
    id: 'agent-001',
    role: 'producer',
    name: 'Kerala Coffee Producer'
  })

  const switchAgent = (agentData) => {
    setCurrentAgent(agentData)
  }

  return (
    <div className="app">
      <div className="header">
        <div className="container">
          <h1>Veritas ORP - Supply Chain Tracker</h1>
          <div className="nav">
            <button
              className={activeTab === 'assertion' ? 'active' : ''}
              onClick={() => setActiveTab('assertion')}
            >
              Create Assertion
            </button>
            <button
              className={activeTab === 'evaluation' ? 'active' : ''}
              onClick={() => setActiveTab('evaluation')}
            >
              Evaluate Claims
            </button>
            <button
              className={activeTab === 'batch' ? 'active' : ''}
              onClick={() => setActiveTab('batch')}
            >
              View Batches
            </button>
          </div>
          <div style={{ textAlign: 'center', marginTop: '15px', opacity: 0.9 }}>
            Current Agent: <strong>{currentAgent.name}</strong> ({currentAgent.role})
            {' | '}
            <select
              value={currentAgent.id}
              onChange={(e) => {
                const agents = {
                  'agent-001': { id: 'agent-001', role: 'producer', name: 'Kerala Coffee Producer' },
                  'agent-002': { id: 'agent-002', role: 'auditor', name: 'Coffee Quality Auditor' },
                  'agent-003': { id: 'agent-003', role: 'logistics', name: 'Logistics Provider' }
                }
                switchAgent(agents[e.target.value])
              }}
              style={{
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                padding: '5px 10px',
                borderRadius: '4px',
                marginLeft: '10px'
              }}
            >
              <option value="agent-001">Switch to Producer</option>
              <option value="agent-002">Switch to Auditor</option>
              <option value="agent-003">Switch to Logistics</option>
            </select>
          </div>
        </div>
      </div>

      <div className="container">
        {activeTab === 'assertion' && (
          <AssertionForm currentAgent={currentAgent} apiUrl={API_URL} />
        )}
        {activeTab === 'evaluation' && (
          <EvaluationPanel currentAgent={currentAgent} apiUrl={API_URL} />
        )}
        {activeTab === 'batch' && (
          <BatchView apiUrl={API_URL} />
        )}
      </div>
    </div>
  )
}

export default App
