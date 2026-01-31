import { Image, ExternalLink, Download, Copy, Check } from 'lucide-react'
import { useState } from 'react'

function LogoCard({ logo }) {
    const [copied, setCopied] = useState(false)

    if (!logo?.found) {
        return (
            <div className="card fade-in delay-2">
                <div className="card-header">
                    <Image size={20} style={{ color: 'var(--accent-primary)' }} />
                    <h3 className="card-title">Logo</h3>
                </div>
                <div className="empty-state" style={{ padding: '2rem' }}>
                    <p className="text-muted">No logo detected</p>
                </div>
            </div>
        )
    }

    // Get SVG data from either svg or svg_data field
    const svgContent = logo.svg || logo.svg_data

    const copySvg = async () => {
        if (svgContent) {
            await navigator.clipboard.writeText(svgContent)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }

    const renderLogo = (bgClass) => {
        // Inline SVG (new format with logo.svg)
        if (svgContent) {
            return (
                <div
                    className={`logo-preview ${bgClass}`}
                    dangerouslySetInnerHTML={{ __html: svgContent }}
                    style={{
                        maxHeight: 120,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '1rem'
                    }}
                />
            )
        }

        // URL-based logo
        if (logo.url) {
            return (
                <div className={`logo-preview ${bgClass}`}>
                    <img
                        src={logo.url}
                        alt="Logo"
                        style={{ maxHeight: 80 }}
                        onError={(e) => { e.target.style.display = 'none' }}
                    />
                </div>
            )
        }

        return null
    }

    return (
        <div className="card fade-in delay-2">
            <div className="card-header">
                <Image size={20} style={{ color: 'var(--accent-primary)' }} />
                <h3 className="card-title">Logo</h3>
                <span className="badge" style={{ marginLeft: 'auto' }}>
                    {logo.type?.toUpperCase()}
                </span>
            </div>

            <div className="logo-display">
                {renderLogo('logo-preview-light')}
                {renderLogo('logo-preview-dark')}
            </div>

            {/* Logo info */}
            {(logo.confidence || logo.source || logo.color) && (
                <div style={{
                    marginTop: '1rem',
                    display: 'flex',
                    gap: '0.5rem',
                    flexWrap: 'wrap',
                    fontSize: '0.75rem'
                }}>
                    {logo.confidence && (
                        <span className="badge">
                            Confidence: {Math.round(logo.confidence * 100)}%
                        </span>
                    )}
                    {logo.source && (
                        <span className="badge">
                            {logo.source}
                        </span>
                    )}
                    {logo.color && (
                        <span className="badge" style={{
                            backgroundColor: logo.color,
                            color: '#fff'
                        }}>
                            {logo.color}
                        </span>
                    )}
                    {logo.is_wordmark && (
                        <span className="badge">Wordmark</span>
                    )}
                </div>
            )}

            {/* Action buttons */}
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                {svgContent && (
                    <button
                        onClick={copySvg}
                        className="btn btn-secondary"
                        style={{ flex: 1 }}
                    >
                        {copied ? <Check size={16} /> : <Copy size={16} />}
                        {copied ? 'Copied!' : 'Copy SVG'}
                    </button>
                )}
                {logo.url && (
                    <>
                        <a
                            href={logo.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary"
                            style={{ flex: 1 }}
                        >
                            <ExternalLink size={16} />
                            Open
                        </a>
                        <a
                            href={logo.url}
                            download
                            className="btn btn-secondary"
                            style={{ flex: 1 }}
                        >
                            <Download size={16} />
                            Download
                        </a>
                    </>
                )}
            </div>
        </div>
    )
}

export default LogoCard
