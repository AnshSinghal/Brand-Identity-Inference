# Brand Identity Inference Engine

A full-stack system designed to reverse-engineer the visual design system of any website in real-time. It extracts the primary logo, color palette (sorted by perceptual dominance), typography hierarchy, and brand "vibe" using a combination of headless browser automation, computer vision, and Large Language Models.

## System Architecture

The application follows a decoupled client-server architecture:

1.  **Frontend (Client)**: A React/Vite Single Page Application (SPA) hosted on Vercel. It serves as the control plane for initiating scans and visualizing the extracted design tokens.
2.  **Backend (API)**: A generic FastAPI service hosted on Render (via Docker). It manages the orchestration of the scraping pipeline, image processing, and LLM inference.
3.  **Headless Browser Layer**: Integrated directly into the backend via Playwright, operating in a highly controlled environment to handle Single Page Applications (SPAs) and hydration states.

## Technical Implementation Details

### 1. Asynchronous Headless Extraction (Playwright)

Unlike traditional HTTP scraping (e.g., `requests` or `BeautifulSoup`), this system must handle modern web applications that rely on client-side rendering (CSR).

*   **Concurrency**: The backend utilizes `async_playwright` to manage a pool of browser contexts. This prevents blocking the FastAPI event loop, allowing the server to handle multiple extraction requests simultaneously without thread locking.
*   **State Management**: The fetcher waits for the `networkidle` state and observes the DOM mutation stability for 500ms before initiating extraction. This ensures that lazy-loaded assets (like logos or fonts) are present in the DOM.
*   **Shadow DOM Traversal**: The extraction script uses recursive Javascript evaluation to pierce Shadow DOM boundaries, ensuring web components are not ignored.

### 2. Logo Detection Pipeline ("Level 9" Heuristics)

Extracting the correct logo is a non-trivial problem due to the ambiguity of the DOM. The system employs a multi-stage voting algorithm:

1.  **Semantic Anchor Analysis**: The system prioritizes `<a>` tags with `href` matching the root domain. It inspects these anchors for `svg` or `img` children.
2.  **SVG Fingerprinting**: Detected SVGs are analyzed for path complexity. Simple SVGs (e.g., search icons, hamburger menus) are discarded based on path length and bounding box aspect ratio (logos are typically rectangular and complex).
3.  **Computer Vision Fallback**: If programmatic extraction yields low confidence, the system captures a viewport screenshot (1440x900), crops the header region, and uses OpenCV to detect the largest significant contour in the top-left quadrant.
4.  **Verification**: The candidate logo is cross-referenced with the site's metadata (OpenGraph tags, Favicon) to produce a final confidence score.

### 3. Perceptual Color Clustering

Raw CSS extraction results in thousands of non-distinct colors. To derive a usable palette:

*   **Extraction**: All computed styles for `background-color`, `color`, and `border-color` are aggregated.
*   **Quantization**: Colors are converted from RGB to the CIE LAB color space to model human color perception.
*   **Clustering**: K-Means clustering is applied to group perceptually similar colors.
*   **Filtering**: Utility colors (pure black/white/gray) are algorithmically deprioritized unless they constitute the majority of the viewable area.

### 4. Large Language Model Integration

For subjective analysis (Brand Vibe), the system pipes extracted text content (Hero headers, Meta descriptions) to the OpenRouter API. This provides a semantic analysis of the brand's tone (e.g., "Professional vs. Playful") which cannot be derived from code alone.

## Deployment Strategy

### Containerization (Docker)
The backend is packaged as a Docker container to ensure the presence of system-level dependencies required by the Chromium browser (e.g., `libnss3`, `libatk`).

*   **Base Image**: `python:3.11-slim`
*   **Package Management**: `uv` is used for high-speed dependency resolution.
*   **Browser Binaries**: Chromium is installed during the build phase to prevent runtime download latencies.

### CI/CD Pipeline
*   **Frontend**: Deployed via Vercel git integration. Environment variables handle API endpoint resolution.
*   **Backend**: Deployed via Render from the Docker registry.
*   **Keep-Alive**: A GitHub Actions cron workflow executes every 14 minutes to ping the `/api/health` endpoint, preventing the Render free-tier instance from entering a sleep state.

## API Reference

### `POST /api/extract`
Initiates a new extraction job.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "logo": {
    "type": "svg",
    "content": "<svg>...</svg>",
    "confidence": 0.95
  },
  "colors": {
    "primary": "#FF5733",
    "secondary": "#33FF57"
  },
  "typography": {
    "heading": "Inter",
    "body": "Roboto"
  }
}
```

## Local Development Requirements

*   Python 3.11+
*   Node.js 18+
*   Docker (Optional, for container testing)

## Installation

1.  **Backend Setup**:
    ```bash
    cd backend
    pip install -r requirements.txt
    playwright install chromium
    uvicorn main:app --reload
    ```

2.  **Frontend Setup**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
