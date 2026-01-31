const API_BASE = import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api`
    : (import.meta.env.PROD ? 'https://brand-identity-inference.onrender.com/api' : '/api')

export async function extractDesignSystem(url) {
    const response = await fetch(`${API_BASE}/extract`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
        },
        body: JSON.stringify({ url }),
        cache: 'no-store',
    })

    if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to extract design system')
    }

    return response.json()
}

export async function getHistory() {
    const response = await fetch(`${API_BASE}/history`)

    if (!response.ok) {
        throw new Error('Failed to load history')
    }

    return response.json()
}

export async function getScan(scanId) {
    const response = await fetch(`${API_BASE}/history/${scanId}`)

    if (!response.ok) {
        throw new Error('Scan not found')
    }

    return response.json()
}

export async function deleteScan(scanId) {
    const response = await fetch(`${API_BASE}/history/${scanId}`, {
        method: 'DELETE',
    })

    if (!response.ok) {
        throw new Error('Failed to delete scan')
    }

    return response.json()
}

export async function clearHistory() {
    const response = await fetch(`${API_BASE}/history`, {
        method: 'DELETE',
    })

    if (!response.ok) {
        throw new Error('Failed to clear history')
    }

    return response.json()
}
