import { useState, useEffect } from 'react'
import axios from 'axios'

function Countdown({ assertionId, apiUrl }) {
  const [timeData, setTimeData] = useState(null)
  const [currentTime, setCurrentTime] = useState(0)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${apiUrl}/assertions/${assertionId}/status`)
        setTimeData(response.data)
        setCurrentTime(response.data.time_elapsed_seconds)
      } catch (error) {
        console.error('Failed to fetch assertion status:', error)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [assertionId, apiUrl])

  useEffect(() => {
    if (!timeData) return

    const timer = setInterval(() => {
      setCurrentTime((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [timeData])

  if (!timeData) {
    return <div className="countdown">Loading...</div>
  }

  const timeRemaining = timeData.deadline_seconds - currentTime
  const percentRemaining = (timeRemaining / timeData.deadline_seconds) * 100

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours}h ${minutes}m ${secs}s`
  }

  let countdownClass = 'countdown'
  if (percentRemaining < 10) {
    countdownClass = 'countdown danger'
  } else if (percentRemaining < 30) {
    countdownClass = 'countdown warning'
  }

  return (
    <div>
      <div className={countdownClass}>
        {timeRemaining > 0 ? (
          <>
            Time Remaining: {formatTime(Math.max(0, timeRemaining))}
            <br />
            <small style={{ fontSize: '0.8rem', opacity: 0.7 }}>
              {percentRemaining.toFixed(1)}% of deadline remaining
            </small>
          </>
        ) : (
          'Deadline Expired'
        )}
      </div>

      <div style={{ marginTop: '10px' }}>
        <div style={{
          width: '100%',
          height: '8px',
          background: '#e5e7eb',
          borderRadius: '4px',
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${Math.max(0, Math.min(100, percentRemaining))}%`,
            height: '100%',
            background: percentRemaining < 10 ? '#ef4444' : percentRemaining < 30 ? '#f59e0b' : '#48bb78',
            transition: 'width 1s linear'
          }} />
        </div>
      </div>
    </div>
  )
}

export default Countdown
