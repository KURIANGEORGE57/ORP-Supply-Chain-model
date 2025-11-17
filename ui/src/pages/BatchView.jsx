import { useState } from 'react'
import Timeline from '../components/Timeline'

function BatchView({ apiUrl }) {
  const [batchId, setBatchId] = useState('batch-99')

  return (
    <div className="card">
      <h2>Batch Timeline View</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        View the complete provenance timeline for a product batch, including assertions, evaluations, and enactments.
      </p>

      <div className="form-group">
        <label>Select Batch</label>
        <select
          value={batchId}
          onChange={(e) => setBatchId(e.target.value)}
        >
          <option value="batch-99">batch-99 (Kerala Premium Arabica)</option>
          <option value="batch-100">batch-100 (Kerala Robusta)</option>
        </select>
      </div>

      <Timeline batchId={batchId} apiUrl={apiUrl} />
    </div>
  )
}

export default BatchView
