import logging
import json
import os
import requests
from typing import Dict

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"  # or "nousresearch/hermes-3-llama-3.1-405b" for OSS


def analyze_tone(hero_text: str, description: str, site_title: str) -> Dict:
    """Analyze website tone/vibe using OpenRouter API."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    # Prepare content
    content = f"Title: {site_title}\nDescription: {description}\nContent: {hero_text}"
    
    # If no content at all, return unknown
    if not content.strip() or len(content) < 20:
        return {
            "tone": "Unknown",
            "audience": "Unknown", 
            "vibe": "Unknown",
            "analysis": "Insufficient content to analyze",
            "success": False
        }
    
    if not api_key:
        logger.warning("No OPENROUTER_API_KEY found")
        return {
            "tone": "Professional",
            "audience": "General",
            "vibe": "Modern",
            "analysis": "No API key available",
            "success": False
        }
    
    try:
        prompt = f"""Analyze this website's tone and target audience based on the following content:

{content[:2000]}

Provide a brief analysis in JSON format:
{{
    "tone": "the overall tone (e.g., Professional, Casual, Playful, Corporate, Friendly, Technical)",
    "audience": "target audience (e.g., Developers, Enterprise, Consumers, Startups, Small Business)",
    "vibe": "overall vibe in 1-2 words (e.g., Modern, Minimalist, Bold, Elegant, Innovative)",
    "analysis": "1-2 sentence summary of the brand personality"
}}

Return ONLY valid JSON, no other text."""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://design-extractor.app",
            "X-Title": "Design System Extractor"
        }
        
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 300
        }
        
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        
        # Clean up response
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
        
        result = json.loads(text)
        result["success"] = True
        
        logger.info(f"Vibe analysis: {result.get('tone')} / {result.get('vibe')}")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in vibe: {e}")
        return {
            "tone": "Professional",
            "audience": "General",
            "vibe": "Modern",
            "analysis": "Could not parse LLM response",
            "success": False
        }
    except Exception as e:
        logger.error(f"Tone analysis error: {e}")
        return {
            "tone": "Professional",
            "audience": "General",
            "vibe": "Modern",
            "analysis": str(e)[:100],
            "success": False
        }
