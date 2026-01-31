import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Palette, History, Sparkles, ChevronRight } from 'lucide-react'
import HomePage from './pages/HomePage'
import HistoryPage from './pages/HistoryPage'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Header() {
    const location = useLocation()

    return (
        <header className="header">
            <div className="container header-content">
                <Link to="/" className="logo">
                    <div className="logo-icon">
                        <Palette size={18} color="white" />
                    </div>
                    <span>DesignThief</span>
                </Link>
                <nav className="nav">
                    <Link
                        to="/"
                        className={`btn btn-ghost ${location.pathname === '/' ? 'btn-secondary' : ''}`}
                    >
                        <Sparkles size={16} />
                        Extract
                    </Link>
                    <Link
                        to="/history"
                        className={`btn btn-ghost ${location.pathname === '/history' ? 'btn-secondary' : ''}`}
                    >
                        <History size={16} />
                        History
                    </Link>
                </nav>
            </div>
        </header>
    )
}

function App() {
    // Warm up backend on initial load
    useEffect(() => {
        const warmUp = async () => {
            try {
                // Determine API URL (fallback to relative if proxied)
                const url = API_URL + '/api/health'
                await fetch(url)
                console.log('Backend warmed up')
            } catch (e) {
                // Silent fail
            }
        }
        warmUp()
    }, [])

    return (
        <BrowserRouter>
            <Header />
            <main className="container">
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/history" element={<HistoryPage />} />
                </Routes>
            </main>
        </BrowserRouter>
    )
}

export default App
