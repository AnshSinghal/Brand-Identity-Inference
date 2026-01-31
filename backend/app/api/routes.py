from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.models import ExtractRequest, DesignSystemResult, ScanHistoryList
from app.extractors.fetcher import WebsiteFetcher
from app.extractors.colors import ColorExtractor
from app.extractors.typography import TypographyExtractor
from app.extractors.logo import LogoExtractor
from app.extractors.llm import analyze_tone
from app.extractors.llm_verify import extract_with_llm
from app import storage

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_and_merge_colors(prog_colors: Dict, llm_result: Dict) -> Dict:
    """Merge colors from programmatic and LLM extraction."""
    llm_colors = {
        "primary": llm_result.get("primary_color"),
        "secondary": llm_result.get("secondary_color"),
        "background": llm_result.get("background_color"),
    }
    
    return {
        "primary": prog_colors.get("primary") or llm_colors.get("primary"),
        "secondary": prog_colors.get("secondary") or llm_colors.get("secondary"),
        "background": prog_colors.get("background") or llm_colors.get("background") or "#ffffff",
        "accent": prog_colors.get("accent"),
        "neutrals": prog_colors.get("neutrals", []),
        "all_colors": prog_colors.get("all_colors", []),
        "primary_source": "programmatic" if prog_colors.get("primary") else ("llm" if llm_colors.get("primary") else "none"),
        "secondary_source": "programmatic" if prog_colors.get("secondary") else ("llm" if llm_colors.get("secondary") else "none"),
        "background_source": "programmatic" if prog_colors.get("background") else ("llm" if llm_colors.get("background") else "default"),
    }


def verify_and_merge_typography(prog_typo: Dict, llm_result: Dict) -> Dict:
    """Merge typography from programmatic and LLM extraction."""
    llm_typo = {
        "heading_font": llm_result.get("heading_font"),
        "body_font": llm_result.get("body_font"),
    }
    
    return {
        "heading_font": prog_typo.get("heading_font") or llm_typo.get("heading_font"),
        "body_font": prog_typo.get("body_font") or llm_typo.get("body_font"),
        "google_fonts": prog_typo.get("google_fonts", []),
        "all_fonts": prog_typo.get("all_fonts", []),
        "heading_source": "programmatic" if prog_typo.get("heading_font") else ("llm" if llm_typo.get("heading_font") else "none"),
        "body_source": "programmatic" if prog_typo.get("body_font") else ("llm" if llm_typo.get("body_font") else "none"),
    }


def verify_and_merge_logo(prog_logo: Dict, llm_result: Dict, base_url: str) -> Dict:
    """Merge logo from programmatic and LLM extraction."""
    llm_logo_url = llm_result.get("logo_url") if llm_result.get("success") else None
    
    # Prefer programmatic if found with decent confidence
    if prog_logo.get("found") and prog_logo.get("confidence", 0) > 0.3:
        return prog_logo
    
    # Use LLM fallback
    if llm_logo_url and "favicon" not in llm_logo_url.lower():
        return {
            "found": True,
            "type": "svg" if ".svg" in llm_logo_url.lower() else "image",
            "svg": None,
            "url": llm_logo_url,
            "color": None,
            "confidence": llm_result.get("logo_confidence", 0.6),
            "source": "llm"
        }
    
    # Return programmatic even if low confidence
    if prog_logo.get("found"):
        return prog_logo
    
    return {
        "found": False,
        "type": None,
        "svg": None,
        "url": None,
        "color": None,
        "confidence": 0,
        "source": "none"
    }


@router.post("/extract", response_model=DesignSystemResult)
async def extract_design_system(request: ExtractRequest):
    url = request.url
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    
    try:
        logger.info(f"========== EXTRACTION START: {url} ==========")
        
        # ===== STEP 1: FETCH WEBSITE (ASYNC) =====
        fetcher = WebsiteFetcher(url, use_playwright=True)
        data = await fetcher.fetch_async()  # Use async fetch!
        
        html = data.get("html", "")
        soup = data.get("soup")
        css = data.get("css", [])
        screenshot = data.get("screenshot")
        brand_anchors = data.get("brand_anchors", [])
        all_svgs = data.get("all_svgs", [])
        header_images = data.get("header_images", [])
        svg_count = data.get("svg_count", 0)
        
        logger.info(f"[FETCH] HTML: {len(html)} bytes, CSS: {len(css)} blocks")
        logger.info(f"[FETCH] Brand Anchors: {len(brand_anchors)}, Header SVGs: {len(all_svgs)}, Header Images: {len(header_images)}, Total SVGs: {svg_count}")
        
        # ===== STEP 2: PROGRAMMATIC EXTRACTION =====
        logger.info("[STEP 2] Running programmatic extraction...")
        
        # Colors
        color_extractor = ColorExtractor(css)
        prog_colors = color_extractor.extract()
        
        # Typography
        typo_extractor = TypographyExtractor(css, html)
        prog_typo = typo_extractor.extract()
        
        # Logo (with full geometry data and vision fallback)
        logo_extractor = LogoExtractor(
            soup=soup,
            base_url=url,
            brand_anchors=brand_anchors,
            all_svgs=all_svgs,
            header_images=header_images,
            screenshot=screenshot
        )
        prog_logo = logo_extractor.extract()
        
        # Meta & Hero
        meta = fetcher.get_meta_info()
        hero_text = fetcher.get_hero_text()
        
        # Vibe (always needs LLM)
        vibe = analyze_tone(
            hero_text=hero_text,
            description=meta.get("description", ""),
            site_title=meta.get("title", "")
        )
        
        logger.info(f"[PROGRAMMATIC] Logo: {prog_logo.get('found')} ({prog_logo.get('source')}, conf={prog_logo.get('confidence')})")
        logger.info(f"[PROGRAMMATIC] Primary: {prog_colors.get('primary')}, Heading: {prog_typo.get('heading_font')}")
        
        # ===== STEP 3: LLM EXTRACTION (ONLY IF NEEDED) =====
        # Skip LLM if programmatic extraction has high confidence
        skip_llm = False
        llm_result = {"success": False}
        
        prog_logo_conf = prog_logo.get("confidence", 0) if prog_logo.get("found") else 0
        has_good_colors = bool(prog_colors.get("primary"))
        has_good_typo = bool(prog_typo.get("heading_font"))
        
        # Only call LLM if we're missing critical data
        if prog_logo_conf >= 0.6 and has_good_colors and has_good_typo:
            skip_llm = True
            logger.info("[STEP 3] SKIPPING LLM - programmatic extraction has high confidence")
        else:
            logger.info("[STEP 3] Running LLM extraction (low confidence or missing data)...")
            css_combined = "\n".join(css[:5])[:30000]
            llm_result = extract_with_llm(html, css_combined, url)
            logger.info(f"[LLM] Success: {llm_result.get('success')}")
            if llm_result.get("success"):
                logger.info(f"[LLM] Logo: {llm_result.get('logo_url')}, Primary: {llm_result.get('primary_color')}")
        
        # ===== STEP 4: VERIFICATION & MERGE =====
        logger.info("[STEP 4] Verifying and merging all results...")
        
        final_colors = verify_and_merge_colors(prog_colors, llm_result)
        final_typo = verify_and_merge_typography(prog_typo, llm_result)
        final_logo = verify_and_merge_logo(prog_logo, llm_result, url)
        
        logger.info(f"[FINAL] Logo: {final_logo.get('source')}, Primary: {final_colors.get('primary_source')}, Heading: {final_typo.get('heading_source')}")
        
        # ===== BUILD RESPONSE =====
        final_result = {
            "url": url,
            "colors": {
                "primary": final_colors.get("primary"),
                "secondary": final_colors.get("secondary"),
                "background": final_colors.get("background"),
                "accent": final_colors.get("accent"),
                "neutrals": final_colors.get("neutrals", []),
                "all_colors": final_colors.get("all_colors", []),
            },
            "typography": {
                "heading_font": final_typo.get("heading_font"),
                "body_font": final_typo.get("body_font"),
                "google_fonts": final_typo.get("google_fonts", []),
                "all_fonts": final_typo.get("all_fonts", []),
            },
            "logo": final_logo,
            "vibe": vibe,
            "meta": meta,
            "hero_text": hero_text,
            "extracted_at": datetime.utcnow().isoformat(),
            
            # === VERIFICATION DEBUG ===
            "verification": {
                "programmatic": {
                    "colors": {
                        "primary": prog_colors.get("primary"),
                        "secondary": prog_colors.get("secondary"),
                        "background": prog_colors.get("background"),
                    },
                    "typography": {
                        "heading_font": prog_typo.get("heading_font"),
                        "body_font": prog_typo.get("body_font"),
                    },
                    "logo": {
                        "found": prog_logo.get("found"),
                        "type": prog_logo.get("type"),
                        "source": prog_logo.get("source"),
                        "confidence": prog_logo.get("confidence"),
                        "is_wordmark": prog_logo.get("is_wordmark"),
                        "has_svg": bool(prog_logo.get("svg")),
                        "url": prog_logo.get("url"),
                    }
                },
                "llm": {
                    "skipped": skip_llm,
                    "success": llm_result.get("success", False),
                    "colors": {
                        "primary": llm_result.get("primary_color"),
                        "secondary": llm_result.get("secondary_color"),
                        "background": llm_result.get("background_color"),
                    },
                    "typography": {
                        "heading_font": llm_result.get("heading_font"),
                        "body_font": llm_result.get("body_font"),
                    },
                    "logo": {
                        "url": llm_result.get("logo_url"),
                        "type": llm_result.get("logo_type"),
                        "confidence": llm_result.get("logo_confidence"),
                    }
                },
                "final": {
                    "colors": {
                        "primary_source": final_colors.get("primary_source"),
                        "secondary_source": final_colors.get("secondary_source"),
                        "background_source": final_colors.get("background_source"),
                    },
                    "typography": {
                        "heading_source": final_typo.get("heading_source"),
                        "body_source": final_typo.get("body_source"),
                    },
                    "logo": {
                        "source": final_logo.get("source"),
                    }
                },
                "stats": {
                    "svg_count": svg_count,
                    "brand_anchors": len(brand_anchors),
                    "header_svgs": len(all_svgs),
                    "header_images": len(header_images),
                }
            }
        }
        
        # ===== SAVE & RETURN =====
        scan_id = storage.save_scan(final_result)
        final_result["id"] = scan_id
        
        logger.info(f"========== EXTRACTION COMPLETE: {url} ==========")
        return final_result
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=ScanHistoryList)
async def get_scan_history():
    scans = storage.get_history()
    return {"scans": scans, "total": len(scans)}


@router.get("/history/{scan_id}")
async def get_scan(scan_id: str):
    result = storage.get_scan_by_id(scan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result


@router.delete("/history/{scan_id}")
async def delete_scan(scan_id: str):
    success = storage.delete_scan(scan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"message": "Deleted"}


@router.delete("/history")
async def clear_all_history():
    count = storage.clear_history()
    return {"message": f"Cleared {count} scans"}
