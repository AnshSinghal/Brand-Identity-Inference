# 🎨 Brand Identity Inference

> AI-powered design system extractor that analyzes any website and extracts its visual identity: logo, colors, typography, and brand vibe.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![React](https://img.shields.io/badge/React-18-61dafb)
![Playwright](https://img.shields.io/badge/Playwright-Chromium-orange)

## ✨ Features

- **🖼️ Logo Extraction** - Brand anchor detection with SVG dominance scoring
- **🎨 Color Analysis** - Extracts primary, secondary, accent, and neutral colors
- **🔤 Typography Detection** - Identifies heading and body fonts, Google Fonts
- **💫 Vibe Analysis** - AI-powered brand personality and tone detection
- **📱 Multi-viewport** - Works across desktop and mobile layouts
- **🔍 2-Step Verification** - Programmatic extraction + LLM validation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                  │
├─────────────────────────────────────────────────────────────┤
│                     Backend (FastAPI + Python)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Fetcher    │  │  Extractors  │  │  LLM Verify  │       │
│  │  (Playwright)│  │ Logo/Colors  │  │ (OpenRouter) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenRouter API key

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Set environment variable
export OPENROUTER_API_KEY=your_key_here

# Run server
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## 🚢 Deployment Options

Since this project requires Playwright (headless browser), Docker-based deployment is recommended.

### Option 1: Render (Free Tier Support)

1. **Frontend**: Deploy `frontend/` to **Vercel** (standard React deploy).
2. **Backend**:
   - Create a **Web Service** on [Render](https://render.com).
   - Connect your GitHub repo.
   - Select **Docker** as the Runtime.
   - Set Root Directory to `backend`.
   - Add Environment Variable: `OPENROUTER_API_KEY`.
   - Use the internal URL provided by Render in your Frontend env vars.

### Option 2: Fly.io (Robust Free Allowance)

1. Install `flyctl`.
2. `cd backend`
3. Run `fly launch` (it will detect the Dockerfile).
4. `fly secrets set OPENROUTER_API_KEY=your_key`
5. `fly deploy`

### Option 3: Hugging Face Spaces (Great for Demos)

1. Create a new Space (Docker SDK).
2. Upload the contents of `backend/` to the root of the Space.
3. Add `OPENROUTER_API_KEY` in settings.

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/extract` | POST | Extract design system from URL |
| `/api/history` | GET | Get scan history |
| `/api/history/{id}` | GET | Get specific scan |
| `/api/history/{id}` | DELETE | Delete scan |
