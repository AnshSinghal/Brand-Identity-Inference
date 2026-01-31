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

## � API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/extract` | POST | Extract design system from URL |
| `/api/history` | GET | Get scan history |
| `/api/history/{id}` | GET | Get specific scan |
| `/api/history/{id}` | DELETE | Delete scan |

### Example Request

```bash
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://stripe.com"}'
```

### Example Response

```json
{
  "url": "https://stripe.com",
  "logo": {
    "found": true,
    "type": "inline_svg",
    "svg": "<svg>...</svg>",
    "confidence": 0.85,
    "source": "brand_anchor_svg"
  },
  "colors": {
    "primary": "#635bff",
    "secondary": "#0a2540",
    "background": "#ffffff"
  },
  "typography": {
    "heading_font": "sohne",
    "body_font": "sohne"
  },
  "vibe": {
    "tone": "Professional",
    "audience": "Developers",
    "vibe": "Modern"
  }
}
```

## � Project Structure

```
Brand-Identity-Inference/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── app/
│   │   ├── api/routes.py    # API endpoints
│   │   ├── models.py        # Pydantic models
│   │   ├── storage.py       # JSON storage
│   │   └── extractors/
│   │       ├── fetcher.py   # Playwright async fetcher
│   │       ├── logo.py      # Logo extraction
│   │       ├── colors.py    # Color extraction
│   │       ├── typography.py # Font extraction
│   │       ├── llm.py       # Vibe analysis
│   │       └── llm_verify.py # LLM verification
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   └── components/
│   ├── package.json
│   └── vite.config.js
├── render.yaml              # Render deployment
└── vercel.json              # Vercel deployment
```

## 🔬 Logo Extraction Pipeline

1. **Brand Anchor Detection** - Find `<a>` elements in header linking to homepage
2. **SVG Dominance Scoring** - Score SVGs by path complexity, aspect ratio, size
3. **Wordmark vs Icon** - Prefer wide SVGs (aspect > 1.5) over square icons
4. **Fingerprint Deduplication** - Skip repeated SVGs (UI icons)
5. **currentColor Resolution** - Resolve CSS colors for SVG logos
6. **Vision Fallback** - OpenCV-based screenshot analysis

## 🚢 Deployment

### Frontend → Vercel
```bash
cd frontend
vercel --prod
```

### Backend → Railway
```bash
# Set OPENROUTER_API_KEY in Railway dashboard
railway up
```

## 📄 License

MIT

## 🙏 Credits

- [FastAPI](https://fastapi.tiangolo.com/)
- [Playwright](https://playwright.dev/)
- [OpenRouter](https://openrouter.ai/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
