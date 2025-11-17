import { useState, useEffect } from 'react'
import axios from 'axios'
import Countdown from '../components/Countdown'

function EvaluationPanel({ currentAgent, apiUrl }) {
  const [assertions, setAssertions] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [selectedAssertion, setSelectedAssertion] = useState(null)
  const [evaluationNotes, setEvaluationNotes] = useState('')

  const loadAssertions = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${apiUrl}/assertions?status=pending`)
      setAssertions(response.data)
    } catch (error) {
      console.error('Failed to load assertions:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAssertions()
    const interval = setInterval(loadAssertions, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [apiUrl])

  const handleEvaluate = async (assertionId, result) => {
    setMessage(null)

    try {
      const evaluationData = {
        id: `eval-${Date.now()}`,
        agent_id: currentAgent.id,
        result: result,
        notes: evaluationNotes,
        signature: null  // In production, would sign with private key
      }

      const response = await axios.post(
        `${apiUrl}/assertions/${assertionId}/evaluations`,
        evaluationData
      )

      setMessage({
        type: 'success',
        text: `Evaluation submitted successfully! Status: ${response.data.status}`
      })

      // Refresh assertions list
      loadAssertions()
      setSelectedAssertion(null)
      setEvaluationNotes('')
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to submit evaluation'
      })
    }
  }

  const getStatusClass = (status) => {
    return `status status-${status}`
  }

  return (
    <div className="card">
      <h2>Pending Evaluations</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Review and evaluate pending assertions. Only assertions matching your role can be evaluated.
      </p>

      {message && (
        <div className={`alert alert-${message.type}`}>
          {message.text}
        </div>
      )}

      {loading && assertions.length === 0 ? (
        <p>Loading assertions...</p>
      ) : assertions.length === 0 ? (
        <div className="alert alert-info">
          No pending assertions found.
        </div>
      ) : (
        <div>
          {assertions.map((assertion) => (
            <div
              key={assertion.id}
              className="list-item"
              onClick={() => setSelectedAssertion(assertion)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong>Assertion ID:</strong> {assertion.id}
                  <br />
                  <strong>Batch:</strong> {assertion.batch_id}
                  <br />
                  <strong>Schema:</strong> {assertion.schema_id}
                  <br />
                  <strong>Score:</strong> {assertion.content_data?.score}
                  <br />
                  <strong>Moisture:</strong> {assertion.content_data?.moisture}
                </div>
                <div>
                  <span className={getStatusClass(assertion.status)}>
                    {assertion.status}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedAssertion && (
        <div className="card" style={{ marginTop: '20px', background: '#f9fafb' }}>
          <h3>Evaluate Assertion: {selectedAssertion.id}</h3>

          <Countdown
            assertionId={selectedAssertion.id}
            apiUrl={apiUrl}
          />

          <div style={{ marginTop: '20px' }}>
            <strong>Batch ID:</strong> {selectedAssertion.batch_id}
            <br />
            <strong>Agent:</strong> {selectedAssertion.agent_id}
            <br />
            <strong>Schema:</strong> {selectedAssertion.schema_id}
            <br />
            <strong>Location:</strong> {selectedAssertion.location_gps}
            <br />
            <strong>Content Data:</strong>
            <pre style={{ background: '#fff', padding: '10px', borderRadius: '4px', marginTop: '10px' }}>
              {JSON.stringify(selectedAssertion.content_data, null, 2)}
            </pre>
          </div>

          <div className="form-group" style={{ marginTop: '20px' }}>
            <label>Evaluation Notes</label>
            <textarea
              value={evaluationNotes}
              onChange={(e) => setEvaluationNotes(e.target.value)}
              placeholder="Add notes about your evaluation..."
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
            <button
              className="btn btn-success"
              onClick={() => handleEvaluate(selectedAssertion.id, true)}
            >
              Approve
            </button>
            <button
              className="btn btn-danger"
              onClick={() => handleEvaluate(selectedAssertion.id, false)}
            >
              Reject
            </button>
            <button
              className="btn"
              style={{ background: '#e5e7eb' }}
              onClick={() => setSelectedAssertion(null)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default EvaluationPanel
