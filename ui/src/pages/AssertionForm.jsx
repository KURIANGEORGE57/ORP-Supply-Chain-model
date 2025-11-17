import { useState } from 'react'
import axios from 'axios'

function AssertionForm({ currentAgent, apiUrl }) {
  const [formData, setFormData] = useState({
    batch_id: 'batch-99',
    schema_id: 'grade_a',
    location_gps: '10.8505,76.2711',
    score: '95',
    moisture: '11%',
    notes: ''
  })
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      const assertionData = {
        id: `assertion-${Date.now()}`,
        batch_id: formData.batch_id,
        agent_id: currentAgent.id,
        schema_id: formData.schema_id,
        location_gps: formData.location_gps,
        content_data: {
          score: parseInt(formData.score),
          moisture: formData.moisture,
          notes: formData.notes
        },
        signature: null  // In production, would sign with private key
      }

      const response = await axios.post(`${apiUrl}/assertions`, assertionData)

      setMessage({
        type: 'success',
        text: `Assertion created successfully! ID: ${response.data.id}`
      })

      // Reset form
      setFormData({
        batch_id: 'batch-99',
        schema_id: 'grade_a',
        location_gps: '10.8505,76.2711',
        score: '95',
        moisture: '11%',
        notes: ''
      })
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to create assertion'
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Create New Assertion</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Submit a quality claim for your coffee batch. This will be evaluated by an auditor within the deadline.
      </p>

      {message && (
        <div className={`alert alert-${message.type}`}>
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Batch ID</label>
          <select
            value={formData.batch_id}
            onChange={(e) => setFormData({ ...formData, batch_id: e.target.value })}
            required
          >
            <option value="batch-99">batch-99 (Kerala Premium Arabica)</option>
            <option value="batch-100">batch-100 (Kerala Robusta)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Schema (Certification Type)</label>
          <select
            value={formData.schema_id}
            onChange={(e) => setFormData({ ...formData, schema_id: e.target.value })}
            required
          >
            <option value="grade_a">Grade A Quality (24h deadline, requires Auditor)</option>
            <option value="logistics_check">Logistics Check (12h deadline, requires Logistics)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Location (GPS)</label>
          <input
            type="text"
            value={formData.location_gps}
            onChange={(e) => setFormData({ ...formData, location_gps: e.target.value })}
            placeholder="10.8505,76.2711"
          />
        </div>

        <div className="form-group">
          <label>Quality Score (0-100)</label>
          <input
            type="number"
            value={formData.score}
            onChange={(e) => setFormData({ ...formData, score: e.target.value })}
            min="0"
            max="100"
            required
          />
        </div>

        <div className="form-group">
          <label>Moisture Content</label>
          <input
            type="text"
            value={formData.moisture}
            onChange={(e) => setFormData({ ...formData, moisture: e.target.value })}
            placeholder="11%"
            required
          />
        </div>

        <div className="form-group">
          <label>Additional Notes</label>
          <textarea
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            placeholder="Any additional information about this batch..."
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Creating...' : 'Create Assertion'}
        </button>
      </form>
    </div>
  )
}

export default AssertionForm
