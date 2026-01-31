import { useState } from 'react'
import { Palette, Copy, Check } from 'lucide-react'

function ColorPalette({ colors }) {
    const [copiedColor, setCopiedColor] = useState(null)

    const copyColor = (color) => {
        navigator.clipboard.writeText(color)
        setCopiedColor(color)
        setTimeout(() => setCopiedColor(null), 1500)
    }

    const mainColors = [
        { key: 'primary', label: 'Primary', color: colors?.primary },
        { key: 'secondary', label: 'Secondary', color: colors?.secondary },
        { key: 'background', label: 'Background', color: colors?.background },
        { key: 'accent', label: 'Accent', color: colors?.accent },
    ].filter(c => c.color)

    return (
        <div className="card fade-in">
            <div className="card-header">
                <Palette size={20} style={{ color: 'var(--accent-primary)' }} />
                <h3 className="card-title">Color Palette</h3>
            </div>

            {/* Main Colors */}
            <div className="palette-grid">
                {mainColors.map(({ key, label, color }) => (
                    <div key={key} className="palette-item">
                        <div
                            className="palette-color"
                            style={{ backgroundColor: color }}
                            onClick={() => copyColor(color)}
                            title={`Click to copy ${color}`}
                        >
                            {copiedColor === color && (
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    height: '100%',
                                    background: 'rgba(0,0,0,0.5)',
                                    borderRadius: 'inherit'
                                }}>
                                    <Check size={20} color="white" />
                                </div>
                            )}
                        </div>
                        <div className="palette-label">{label}</div>
                        <div className="palette-value">{color}</div>
                    </div>
                ))}
            </div>

            {/* Neutrals */}
            {colors?.neutrals?.length > 0 && (
                <div style={{ marginTop: '1.5rem' }}>
                    <div className="palette-label" style={{ marginBottom: '0.5rem' }}>Neutrals</div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {colors.neutrals.slice(0, 5).map((color, i) => (
                            <div
                                key={i}
                                style={{
                                    width: 32,
                                    height: 32,
                                    borderRadius: 6,
                                    backgroundColor: color,
                                    border: '1px solid var(--border-color)',
                                    cursor: 'pointer'
                                }}
                                onClick={() => copyColor(color)}
                                title={color}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* All Colors (expandable) */}
            {colors?.all_colors?.length > 0 && (
                <details style={{ marginTop: '1rem' }}>
                    <summary style={{
                        cursor: 'pointer',
                        color: 'var(--text-muted)',
                        fontSize: '0.875rem'
                    }}>
                        View all {colors.all_colors.length} colors
                    </summary>
                    <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.5rem',
                        marginTop: '0.75rem'
                    }}>
                        {colors.all_colors.map(({ color, count }, i) => (
                            <div
                                key={i}
                                style={{
                                    width: 24,
                                    height: 24,
                                    borderRadius: 4,
                                    backgroundColor: color,
                                    border: '1px solid var(--border-color)',
                                    cursor: 'pointer'
                                }}
                                onClick={() => copyColor(color)}
                                title={`${color} (used ${count}x)`}
                            />
                        ))}
                    </div>
                </details>
            )}
        </div>
    )
}

export default ColorPalette
