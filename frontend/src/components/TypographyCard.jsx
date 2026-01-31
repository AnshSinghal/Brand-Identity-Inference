import { Type } from 'lucide-react'

function TypographyCard({ typography }) {
    const headingFont = typography?.heading_font || 'Not detected'
    const bodyFont = typography?.body_font || 'Not detected'
    const googleFonts = typography?.google_fonts || []

    return (
        <div className="card fade-in delay-1">
            <div className="card-header">
                <Type size={20} style={{ color: 'var(--accent-primary)' }} />
                <h3 className="card-title">Typography</h3>
            </div>

            {/* Heading Font */}
            <div className="font-preview">
                <div className="font-label">Heading Font</div>
                <div className="font-name">{headingFont}</div>
                <div
                    className="font-sample"
                    style={{ fontFamily: headingFont !== 'Not detected' ? headingFont : 'inherit' }}
                >
                    The quick brown fox
                </div>
            </div>

            {/* Body Font */}
            <div className="font-preview">
                <div className="font-label">Body Font</div>
                <div className="font-name">{bodyFont}</div>
                <div
                    className="font-sample"
                    style={{
                        fontFamily: bodyFont !== 'Not detected' ? bodyFont : 'inherit',
                        fontSize: '1rem'
                    }}
                >
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                </div>
            </div>

            {/* Google Fonts */}
            {googleFonts.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                    <div className="font-label">Google Fonts Detected</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                        {googleFonts.map((font, i) => (
                            <span key={i} className="badge">{font}</span>
                        ))}
                    </div>
                </div>
            )}

            {/* All Fonts */}
            {typography?.all_fonts?.length > 0 && (
                <details style={{ marginTop: '1rem' }}>
                    <summary style={{
                        cursor: 'pointer',
                        color: 'var(--text-muted)',
                        fontSize: '0.875rem'
                    }}>
                        View all {typography.all_fonts.length} fonts
                    </summary>
                    <div style={{ marginTop: '0.75rem' }}>
                        {typography.all_fonts.map(({ font, count }, i) => (
                            <div
                                key={i}
                                style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    padding: '0.25rem 0',
                                    borderBottom: '1px solid var(--border-color)'
                                }}
                            >
                                <span>{font}</span>
                                <span className="text-muted">{count}x</span>
                            </div>
                        ))}
                    </div>
                </details>
            )}
        </div>
    )
}

export default TypographyCard
