import { useState, useEffect } from 'react'
import axios from 'axios'
import { formatDistanceToNow } from 'date-fns'

function Timeline({ batchId, apiUrl }) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const loadBatchHistory = async () => {
      setLoading(true)
      try {
        // In a real implementation, we'd have a dedicated endpoint for batch history
        // For now, we'll fetch assertions and build the timeline
        const response = await axios.get(`${apiUrl}/assertions?status=pending`)
        const batchAssertions = response.data.filter(a => a.batch_id === batchId)

        // Build timeline events
        const timelineEvents = batchAssertions.map(assertion => ({
          type: 'assertion',
          id: assertion.id,
          timestamp: assertion.timestamp,
          data: assertion
        }))

        setEvents(timelineEvents.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)))
      } catch (error) {
        console.error('Failed to load batch history:', error)
      } finally {
        setLoading(false)
      }
    }

    if (batchId) {
      loadBatchHistory()
    }
  }, [batchId, apiUrl])

  const getStatusClass = (status) => {
    return `status status-${status}`
  }

  if (loading) {
    return <div>Loading timeline...</div>
  }

  if (events.length === 0) {
    return (
      <div className="alert alert-info">
        No events found for this batch yet.
      </div>
    )
  }

  return (
    <div className="timeline">
      {events.map((event, index) => (
        <div key={event.id} className="timeline-item">
          {event.type === 'assertion' && (
            <div>
              <h4>Assertion Created</h4>
              <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '10px' }}>
                {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
              </p>
              <div style={{ background: '#fff', padding: '15px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                <div style={{ marginBottom: '10px' }}>
                  <span className={getStatusClass(event.data.status)}>
                    {event.data.status}
                  </span>
                </div>
                <strong>ID:</strong> {event.data.id}
                <br />
                <strong>Agent:</strong> {event.data.agent_id}
                <br />
                <strong>Schema:</strong> {event.data.schema_id}
                <br />
                <strong>Location:</strong> {event.data.location_gps}
                <br />
                <details style={{ marginTop: '10px' }}>
                  <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                    View Content Data
                  </summary>
                  <pre style={{ background: '#f9fafb', padding: '10px', borderRadius: '4px', marginTop: '10px', fontSize: '0.85rem' }}>
                    {JSON.stringify(event.data.content_data, null, 2)}
                  </pre>
                </details>
                {event.data.signature && (
                  <>
                    <br />
                    <strong>Signature:</strong>
                    <code style={{ fontSize: '0.8rem', display: 'block', marginTop: '5px', wordBreak: 'break-all' }}>
                      {event.data.signature.substring(0, 60)}...
                    </code>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default Timeline
