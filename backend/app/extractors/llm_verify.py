import json
import logging
import os
import re
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"  # Fast and cheap


def chunk_text(text: str, chunk_size: int = 6000) -> List[str]:
    """Split text into chunks of approximately chunk_size characters."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        end_pos = min(current_pos + chunk_size, len(text))
        
        # Try to break at a newline for cleaner chunks
        if end_pos < len(text):
            newline_pos = text.rfind('\n', current_pos, end_pos)
            if newline_pos > current_pos + chunk_size // 2:
                end_pos = newline_pos + 1
        
        chunks.append(text[current_pos:end_pos])
        current_pos = end_pos
    
    return chunks


def _call_openrouter(prompt: str, max_tokens: int = 400) -> Optional[str]:
    """Make a call to OpenRouter API."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://design-extractor.app",
        "X-Title": "Design System Extractor"
    }
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        return None


def extract_with_llm(html: str, css_snippets: str, base_url: str) -> Dict:
    """
    Extract design system using LLM with chunked processing.
    Sends full HTML and CSS in chunks to get comprehensive analysis.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        return {"success": False, "error": "No API key"}
    
    if not html or len(html) < 200:
        return {"success": False, "error": "Insufficient HTML"}
    
    try:
        # Parse HTML for structured extraction
        soup = BeautifulSoup(html, 'lxml')
        
        # === PHASE 1: Extract key sections ===
        
        # Header section (most important for logo)
        header = soup.find(["header", "nav", "[role='banner']"])
        header_html = str(header)[:8000] if header else ""
        
        # All images with context
        all_images = []
        for img in soup.find_all("img", src=True)[:20]:
            parent = img.find_parent(["a", "div", "header", "nav"])
            parent_info = ""
            if parent:
                parent_info = f"Parent: <{parent.name} class='{' '.join(parent.get('class', []))}' href='{parent.get('href', '')}'>"
            
            all_images.append({
                "src": img.get("src"),
                "alt": img.get("alt", ""),
                "class": " ".join(img.get("class", [])),
                "parent": parent_info
            })
        
        # All SVGs in header/nav
        header_svgs = []
        if header:
            for svg in header.find_all("svg")[:5]:
                paths = svg.find_all("path")
                header_svgs.append({
                    "path_count": len(paths),
                    "total_d_length": sum(len(p.get("d", "")) for p in paths),
                    "html_preview": str(svg)[:500]
                })
        
        # === PHASE 2: Chunk CSS and extract colors/fonts ===
        css_chunks = chunk_text(css_snippets, 8000)
        
        # === PHASE 3: First LLM call - Logo and Structure ===
        logo_prompt = f"""Analyze this website's header and images to find the MAIN LOGO.

URL: {base_url}

HEADER HTML:
{header_html[:6000]}

ALL IMAGES ON PAGE:
{json.dumps(all_images, indent=2)[:3000]}

SVGs IN HEADER:
{json.dumps(header_svgs, indent=2)}

RULES:
1. The logo is usually in header/nav
2. Logo links to homepage (href="/" or domain)
3. Ignore favicons (16x16, 32x32)
4. Ignore social icons, app store badges
5. Prefer SVG over PNG
6. Look for "logo" in alt, class, or src

Return ONLY valid JSON:
{{
    "logo_url": "full absolute URL to main logo image, or null if inline SVG",
    "logo_type": "svg" | "png" | "image" | "inline_svg",
    "logo_in_header": true | false,
    "confidence": 0.0 to 1.0
}}"""

        logo_text = _call_openrouter(logo_prompt, 400)
        logo_result = _parse_json_response(logo_text) if logo_text else None
        
        # === PHASE 4: Second LLM call - Colors from CSS ===
        colors_found = []
        
        for i, css_chunk in enumerate(css_chunks[:2]):  # Process up to 2 CSS chunks
            colors_prompt = f"""Extract the PRIMARY BRAND COLORS from this CSS (chunk {i+1}/{len(css_chunks[:2])}).

CSS:
{css_chunk}

Focus on:
- Button backgrounds (primary action color)
- Link colors
- Heading colors
- Brand color variables
- Background colors

Ignore:
- Black, white, gray (neutrals)
- Transparent
- var() references

Return ONLY valid JSON:
{{
    "primary_color": "#hex or null",
    "secondary_color": "#hex or null", 
    "background_color": "#hex or null",
    "accent_color": "#hex or null"
}}"""

            try:
                colors_text = _call_openrouter(colors_prompt, 200)
                if colors_text:
                    chunk_colors = _parse_json_response(colors_text)
                    if chunk_colors:
                        colors_found.append(chunk_colors)
            except:
                pass
        
        # Merge color results (pick first non-null for each)
        merged_colors = {
            "primary_color": None,
            "secondary_color": None,
            "background_color": None
        }
        for cf in colors_found:
            if not merged_colors["primary_color"] and cf.get("primary_color"):
                merged_colors["primary_color"] = cf["primary_color"]
            if not merged_colors["secondary_color"] and cf.get("secondary_color"):
                merged_colors["secondary_color"] = cf["secondary_color"]
            if not merged_colors["background_color"] and cf.get("background_color"):
                merged_colors["background_color"] = cf["background_color"]
        
        # === PHASE 5: Third LLM call - Typography ===
        typo_prompt = f"""Extract the FONT FAMILIES used on this website.

CSS (first chunk):
{css_chunks[0][:5000] if css_chunks else ""}

HTML HEAD (for Google Fonts):
{str(soup.head)[:3000] if soup.head else ""}

Look for:
- font-family declarations
- Google Fonts imports
- @font-face declarations

Ignore:
- Icon fonts (FontAwesome, Material Icons)
- System fonts (Arial, Helvetica, sans-serif)
- var() references

Return ONLY valid JSON:
{{
    "heading_font": "font name or null",
    "body_font": "font name or null",
    "google_fonts": ["font1", "font2"]
}}"""

        typo_text = _call_openrouter(typo_prompt, 300)
        typo_result = _parse_json_response(typo_text) if typo_text else None
        
        # === COMBINE ALL RESULTS ===
        final_result = {
            "success": True,
            "logo_url": logo_result.get("logo_url") if logo_result else None,
            "logo_type": logo_result.get("logo_type") if logo_result else None,
            "logo_confidence": logo_result.get("confidence", 0) if logo_result else 0,
            "primary_color": merged_colors.get("primary_color"),
            "secondary_color": merged_colors.get("secondary_color"),
            "background_color": merged_colors.get("background_color"),
            "heading_font": typo_result.get("heading_font") if typo_result else None,
            "body_font": typo_result.get("body_font") if typo_result else None,
            "google_fonts": typo_result.get("google_fonts", []) if typo_result else [],
        }
        
        logger.info(f"[LLM] Chunked extraction complete: logo={final_result.get('logo_url')}, primary={final_result.get('primary_color')}")
        
        return final_result
        
    except Exception as e:
        logger.error(f"LLM extraction error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)[:200]}


def _parse_json_response(text: str) -> Optional[Dict]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    if not text:
        return None
    
    try:
        # Remove markdown code blocks
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
        
        return json.loads(text)
    except:
        # Try to extract JSON from text
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return None
