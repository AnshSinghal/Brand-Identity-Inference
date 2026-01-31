import { useState } from 'react'
import { Search, Loader2, Download, Copy, Check, ExternalLink } from 'lucide-react'
import { extractDesignSystem } from '../api'
import ColorPalette from '../components/ColorPalette'
import TypographyCard from '../components/TypographyCard'
import LogoCard from '../components/LogoCard'
import VibeCard from '../components/VibeCard'

function HomePage() {
    const [url, setUrl] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [result, setResult] = useState(null)
    const [copied, setCopied] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!url.trim()) return

        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const data = await extractDesignSystem(url)
            setResult(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const copyJSON = () => {
        navigator.clipboard.writeText(JSON.stringify(result, null, 2))
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const downloadJSON = () => {
        const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `design-system-${result.meta?.title || 'export'}.json`
        a.click()
        URL.revokeObjectURL(url)
    }

    return (
        <div>
            {/* Hero Section */}
            <section className="hero">
                <h1 className="hero-title">Design System Extractor</h1>
                <p className="hero-subtitle">
                    Enter any URL and steal their furniture (legally). Extract colors, fonts, logos, and analyze their brand vibe.
                </p>

                <form className="hero-form" onSubmit={handleSubmit}>
                    <div className="input-group">
                        <input
                            type="text"
                            className="input input-lg"
                            placeholder="https://example.com"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary btn-lg"
                            disabled={loading || !url.trim()}
                        >
                            {loading ? (
                                <Loader2 size={20} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                            ) : (
                                <Search size={20} />
                            )}
                            {loading ? 'Extracting...' : 'Extract'}
                        </button>
                    </div>
                </form>

                {error && (
                    <div className="card" style={{ marginTop: '1rem', borderColor: 'var(--error)' }}>
                        <p style={{ color: 'var(--error)' }}>{error}</p>
                    </div>
                )}
            </section>

            {/* Loading State */}
            {loading && (
                <section className="results fade-in">
                    <div className="results-grid">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="card">
                                <div className="skeleton" style={{ height: 24, width: '40%', marginBottom: 16 }} />
                                <div className="skeleton" style={{ height: 100, marginBottom: 12 }} />
                                <div className="skeleton" style={{ height: 16, width: '60%' }} />
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* Results */}
            {result && !loading && (
                <section className="results">
                    <div className="results-header">
                        <div>
                            <h2 className="results-title">{result.meta?.title || result.url}</h2>
                            <a
                                href={result.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-muted"
                                style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                            >
                                {result.url} <ExternalLink size={14} />
                            </a>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button className="btn btn-secondary" onClick={copyJSON}>
                                {copied ? <Check size={16} /> : <Copy size={16} />}
                                {copied ? 'Copied!' : 'Copy JSON'}
                            </button>
                            <button className="btn btn-secondary" onClick={downloadJSON}>
                                <Download size={16} />
                                Download
                            </button>
                        </div>
                    </div>

                    <div className="results-grid">
                        <ColorPalette colors={result.colors} />
                        <TypographyCard typography={result.typography} />
                        <LogoCard logo={result.logo} />
                        <VibeCard vibe={result.vibe} heroText={result.hero_text} />
                    </div>

                    {/* Raw JSON Preview */}
                    <div className="card fade-in delay-4" style={{ marginTop: '1.5rem' }}>
                        <div className="card-header">
                            <h3 className="card-title">Raw JSON Output</h3>
                        </div>
                        <pre className="json-preview">
                            {JSON.stringify(result, null, 2)}
                        </pre>
                    </div>
                </section>
            )}
        </div>
    )
}

export default HomePage
