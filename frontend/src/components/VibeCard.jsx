import { Sparkles, Users, Zap, MessageCircle } from 'lucide-react'

function VibeCard({ vibe, heroText }) {
    if (!vibe?.success && !vibe?.tone) {
        return (
            <div className="card fade-in delay-3">
                <div className="card-header">
                    <Sparkles size={20} style={{ color: 'var(--accent-primary)' }} />
                    <h3 className="card-title">Vibe Check</h3>
                </div>
                <div style={{ padding: '1rem', textAlign: 'center' }}>
                    <p className="text-muted">
                        {vibe?.analysis || 'Configure GEMINI_API_KEY to enable tone analysis'}
                    </p>
                </div>
            </div>
        )
    }

    return (
        <div className="card fade-in delay-3">
            <div className="card-header">
                <Sparkles size={20} style={{ color: 'var(--accent-primary)' }} />
                <h3 className="card-title">Vibe Check</h3>
                {vibe?.success && (
                    <span className="badge badge-success" style={{ marginLeft: 'auto' }}>
                        AI Analyzed
                    </span>
                )}
            </div>

            <div className="vibe-grid">
                <div className="vibe-item">
                    <MessageCircle size={20} style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }} />
                    <div className="vibe-label">Tone</div>
                    <div className="vibe-value">{vibe?.tone || 'Unknown'}</div>
                </div>

                <div className="vibe-item">
                    <Users size={20} style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }} />
                    <div className="vibe-label">Audience</div>
                    <div className="vibe-value">{vibe?.audience || 'Unknown'}</div>
                </div>

                <div className="vibe-item">
                    <Zap size={20} style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }} />
                    <div className="vibe-label">Vibe</div>
                    <div className="vibe-value">{vibe?.vibe || 'Unknown'}</div>
                </div>
            </div>

            {vibe?.analysis && (
                <div style={{
                    marginTop: '1rem',
                    padding: '1rem',
                    background: 'var(--bg-secondary)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.875rem',
                    color: 'var(--text-secondary)'
                }}>
                    {vibe.analysis}
                </div>
            )}

            {heroText && (
                <details style={{ marginTop: '1rem' }}>
                    <summary style={{
                        cursor: 'pointer',
                        color: 'var(--text-muted)',
                        fontSize: '0.875rem'
                    }}>
                        View analyzed text
                    </summary>
                    <div style={{
                        marginTop: '0.5rem',
                        padding: '0.75rem',
                        background: 'var(--bg-secondary)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.875rem',
                        fontStyle: 'italic',
                        color: 'var(--text-muted)'
                    }}>
                        "{heroText}"
                    </div>
                </details>
            )}
        </div>
    )
}

export default VibeCard
