import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Clock, Trash2, ArrowRight, FolderOpen } from 'lucide-react'
import { getHistory, deleteScan, clearHistory, getScan } from '../api'

function HistoryPage() {
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [selectedScan, setSelectedScan] = useState(null)

    useEffect(() => {
        loadHistory()
    }, [])

    const loadHistory = async () => {
        try {
            const data = await getHistory()
            setHistory(data.scans || [])
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async (e, scanId) => {
        e.stopPropagation()
        try {
            await deleteScan(scanId)
            setHistory(history.filter(s => s.id !== scanId))
        } catch (err) {
            console.error(err)
        }
    }

    const handleClearAll = async () => {
        if (confirm('Are you sure you want to clear all history?')) {
            try {
                await clearHistory()
                setHistory([])
            } catch (err) {
                console.error(err)
            }
        }
    }

    const handleViewScan = async (scanId) => {
        try {
            const data = await getScan(scanId)
            setSelectedScan(data)
        } catch (err) {
            console.error(err)
        }
    }

    const formatDate = (timestamp) => {
        const date = new Date(timestamp)
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
                <div className="loader" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="card" style={{ textAlign: 'center' }}>
                <p style={{ color: 'var(--error)' }}>{error}</p>
            </div>
        )
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '2rem', fontWeight: 600 }}>Scan History</h1>
                {history.length > 0 && (
                    <button className="btn btn-secondary" onClick={handleClearAll}>
                        <Trash2 size={16} />
                        Clear All
                    </button>
                )}
            </div>

            {history.length === 0 ? (
                <div className="empty-state">
                    <FolderOpen size={64} className="empty-icon" />
                    <h3 className="empty-title">No scans yet</h3>
                    <p className="empty-text">Extract your first design system to see it here.</p>
                    <Link to="/" className="btn btn-primary" style={{ marginTop: '1rem' }}>
                        Start Extracting
                    </Link>
                </div>
            ) : (
                <div className="history-grid">
                    {history.map((scan) => (
                        <div
                            key={scan.id}
                            className="card history-card"
                            onClick={() => handleViewScan(scan.id)}
                        >
                            <div
                                className="history-color"
                                style={{
                                    background: scan.primary_color || 'var(--bg-secondary)',
                                    border: '1px solid var(--border-color)'
                                }}
                            />
                            <div className="history-info">
                                <div className="history-title">{scan.title || 'Untitled'}</div>
                                <div className="history-url">{scan.url}</div>
                                <div className="history-time">
                                    <Clock size={12} style={{ display: 'inline', marginRight: 4 }} />
                                    {formatDate(scan.timestamp)}
                                </div>
                            </div>
                            <button
                                className="btn btn-ghost"
                                onClick={(e) => handleDelete(e, scan.id)}
                                title="Delete scan"
                            >
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Selected Scan Modal/Preview */}
            {selectedScan && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0,0,0,0.8)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                        padding: '2rem'
                    }}
                    onClick={() => setSelectedScan(null)}
                >
                    <div
                        className="card"
                        style={{
                            maxWidth: 800,
                            maxHeight: '80vh',
                            overflow: 'auto',
                            width: '100%'
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <h2>{selectedScan.meta?.title || selectedScan.url}</h2>
                            <button className="btn btn-ghost" onClick={() => setSelectedScan(null)}>✕</button>
                        </div>

                        {/* Color preview */}
                        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                            {['primary', 'secondary', 'background', 'accent'].map((key) => (
                                selectedScan.colors?.[key] && (
                                    <div key={key} style={{ textAlign: 'center' }}>
                                        <div
                                            style={{
                                                width: 60,
                                                height: 60,
                                                borderRadius: 8,
                                                background: selectedScan.colors[key],
                                                border: '1px solid var(--border-color)'
                                            }}
                                        />
                                        <div className="text-muted" style={{ fontSize: 12, marginTop: 4 }}>{key}</div>
                                        <div style={{ fontSize: 11, fontFamily: 'monospace' }}>{selectedScan.colors[key]}</div>
                                    </div>
                                )
                            ))}
                        </div>

                        {/* Typography */}
                        <div style={{ marginBottom: '1rem' }}>
                            <strong>Fonts:</strong>{' '}
                            {selectedScan.typography?.heading_font && <span>{selectedScan.typography.heading_font}</span>}
                            {selectedScan.typography?.body_font && <span> / {selectedScan.typography.body_font}</span>}
                        </div>

                        {/* Vibe */}
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            {selectedScan.vibe && (
                                <>
                                    <span className="badge">Tone: {selectedScan.vibe.tone}</span>
                                    <span className="badge">Audience: {selectedScan.vibe.audience}</span>
                                    <span className="badge">Vibe: {selectedScan.vibe.vibe}</span>
                                </>
                            )}
                        </div>

                        <pre className="json-preview" style={{ marginTop: '1rem' }}>
                            {JSON.stringify(selectedScan, null, 2)}
                        </pre>
                    </div>
                </div>
            )}
        </div>
    )
}

export default HistoryPage
