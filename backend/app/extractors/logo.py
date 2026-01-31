import re
import logging
import base64
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import defaultdict

logger = logging.getLogger(__name__)


def rgb_to_hex(rgb_string: str) -> Optional[str]:
    """Convert rgb(r, g, b) to #hex."""
    match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', rgb_string)
    if match:
        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return f"#{r:02x}{g:02x}{b:02x}"
    return None


class LogoExtractor:
    """
    Brand Anchor Logo Architecture with Vision Fallback.
    
    Pipeline:
    1. Extract from brand anchors (highest priority)
    2. Extract from header SVGs
    3. Extract from header images
    4. DOM fallback
    5. Vision fallback (screenshot analysis)
    
    Features:
    - SVG fingerprint deduplication (UI icons are repeated, logos are unique)
    - Brand anchor confidence boost
    - Wordmark preference over icons
    """
    
    def __init__(self, soup: BeautifulSoup, base_url: str, 
                 brand_anchors: List[Dict] = None,
                 all_svgs: List[Dict] = None,
                 header_images: List[Dict] = None,
                 screenshot: Optional[str] = None):
        self.soup = soup
        self.base_url = base_url
        self.origin = urlparse(base_url).scheme + "://" + urlparse(base_url).netloc
        self.brand_anchors = brand_anchors or []
        self.all_svgs = all_svgs or []
        self.header_images = header_images or []
        self.screenshot = screenshot
        
        # Build SVG fingerprint usage map for deduplication
        self.svg_fingerprint_usage = self._build_fingerprint_map()
    
    def _build_fingerprint_map(self) -> Dict[str, int]:
        """Build a map of SVG fingerprints to their usage count.
        UI icons repeat many times, logos are usually unique."""
        usage = defaultdict(int)
        
        # From brand anchors
        for anchor in self.brand_anchors:
            for svg in anchor.get("svgs", []):
                fp = svg.get("geometry", {}).get("fingerprint", "")
                if fp:
                    usage[fp] += 1
        
        # From all SVGs
        for svg in self.all_svgs:
            fp = svg.get("geometry", {}).get("fingerprint", "")
            if fp:
                usage[fp] += 1
        
        # From DOM if available
        if self.soup:
            for svg in self.soup.find_all("svg"):
                paths = svg.find_all("path")
                fp = "".join(p.get("d", "")[:50] for p in paths)[:200]
                if fp:
                    usage[fp] += 1
        
        return dict(usage)
    
    def extract(self) -> Dict:
        """Extract logo using multi-tier approach with deduplication."""
        
        # TIER 1: Brand Anchor SVGs (highest priority)
        logo = self._extract_from_brand_anchors()
        if logo and logo.get("found") and logo.get("confidence", 0) > 0.5:
            logger.info(f"Logo found via brand anchor: {logo.get('source')}")
            return logo
        
        # TIER 2: All Header SVGs
        if not logo or not logo.get("found"):
            logo = self._extract_from_header_svgs()
            if logo and logo.get("found") and logo.get("confidence", 0) > 0.4:
                logger.info(f"Logo found via header SVG")
                return logo
        
        # TIER 3: Header Images
        if not logo or not logo.get("found"):
            logo = self._extract_from_header_images()
            if logo and logo.get("found"):
                logger.info(f"Logo found via header image")
                return logo
        
        # TIER 4: DOM Fallback
        if not logo or not logo.get("found"):
            logo = self._fallback_dom_extraction()
            if logo and logo.get("found"):
                logger.info(f"Logo found via DOM fallback")
                return logo
        
        # TIER 5: Vision Fallback
        if self.screenshot:
            logo = self._vision_fallback()
            if logo and logo.get("found"):
                logger.info(f"Logo found via vision fallback")
                return logo
        
        # No logo found
        return {
            "found": False,
            "type": None,
            "svg": None,
            "url": None,
            "color": None,
            "confidence": 0,
            "source": "none"
        }
    
    def _is_repeated_svg(self, fingerprint: str) -> bool:
        """Check if SVG fingerprint appears multiple times (likely UI icon)."""
        if not fingerprint:
            return False
        return self.svg_fingerprint_usage.get(fingerprint, 0) > 1
    
    def _extract_from_brand_anchors(self) -> Optional[Dict]:
        """Extract logo from brand anchor with SVG dominance scoring."""
        
        best_logo = None
        best_score = 0
        
        for anchor in self.brand_anchors:
            # Process SVGs first (preferred)
            for svg_data in anchor.get("svgs", []):
                geometry = svg_data.get("geometry", {})
                fingerprint = geometry.get("fingerprint", "")
                
                # Skip repeated SVGs (UI icons)
                if self._is_repeated_svg(fingerprint):
                    logger.debug(f"Skipping repeated SVG (likely UI icon)")
                    continue
                
                score = self._calculate_svg_score(geometry, svg_data)
                
                if score > best_score:
                    best_score = score
                    
                    # Resolve color
                    color = None
                    colors = svg_data.get("colors", {})
                    if colors.get("color"):
                        color = rgb_to_hex(colors["color"]) or colors["color"]
                    elif colors.get("fill") and colors["fill"] != "none":
                        color = rgb_to_hex(colors["fill"]) or colors["fill"]
                    
                    # Brand anchor SVGs get minimum 0.75 confidence
                    confidence = max(0.75, min(0.95, score / 100))
                    
                    best_logo = {
                        "found": True,
                        "type": "inline_svg",
                        "svg": svg_data.get("html"),
                        "url": None,
                        "color": color,
                        "confidence": confidence,
                        "source": "brand_anchor_svg",
                        "is_wordmark": geometry.get("isWordmark", False),
                        "complexity": {
                            "path_count": geometry.get("pathCount", 0),
                            "path_length": geometry.get("totalPathLength", 0),
                            "aspect_ratio": round(geometry.get("aspectRatio", 1), 2)
                        }
                    }
            
            # Process images if no good SVG
            if best_score < 40:
                for img_data in anchor.get("imgs", []):
                    src = img_data.get("src")
                    if not src:
                        continue
                    
                    score = self._calculate_image_score(img_data)
                    
                    if score > best_score:
                        best_score = score
                        
                        # Brand anchor images get minimum 0.65 confidence
                        confidence = max(0.65, min(0.85, score / 100))
                        
                        best_logo = {
                            "found": True,
                            "type": "svg" if ".svg" in src.lower() else "image",
                            "svg": None,
                            "url": urljoin(self.base_url, src),
                            "color": None,
                            "confidence": confidence,
                            "source": "brand_anchor_img"
                        }
        
        return best_logo
    
    def _extract_from_header_svgs(self) -> Optional[Dict]:
        """Extract logo from all header SVGs."""
        
        best_logo = None
        best_score = 0
        
        for svg_data in self.all_svgs:
            geometry = svg_data.get("geometry", {})
            fingerprint = geometry.get("fingerprint", "")
            
            # Skip repeated SVGs
            if self._is_repeated_svg(fingerprint):
                continue
            
            in_link = svg_data.get("isInLink", False)
            
            score = self._calculate_svg_score(geometry, svg_data)
            if not in_link:
                score *= 0.7  # Penalty for not being in a link
            
            if score > best_score:
                best_score = score
                
                color = None
                colors = svg_data.get("colors", {})
                if colors.get("color"):
                    color = rgb_to_hex(colors["color"]) or colors["color"]
                
                best_logo = {
                    "found": True,
                    "type": "inline_svg",
                    "svg": svg_data.get("html"),
                    "url": None,
                    "color": color,
                    "confidence": min(0.8, score / 100),
                    "source": "header_svg",
                    "is_wordmark": geometry.get("isWordmark", False)
                }
        
        return best_logo
    
    def _extract_from_header_images(self) -> Optional[Dict]:
        """Extract logo from header images."""
        
        best_logo = None
        best_score = 0
        
        for img_data in self.header_images:
            score = self._calculate_image_score(img_data)
            
            # Bonus for being in a home link
            link_href = img_data.get("linkHref", "")
            if link_href in ["/", self.origin, self.origin + "/"]:
                score += 25
            
            if score > best_score:
                best_score = score
                src = img_data.get("src")
                
                best_logo = {
                    "found": True,
                    "type": "svg" if ".svg" in src.lower() else "image",
                    "svg": None,
                    "url": urljoin(self.base_url, src),
                    "color": None,
                    "confidence": min(0.75, score / 100),
                    "source": "header_image"
                }
        
        return best_logo
    
    def _calculate_svg_score(self, geometry: Dict, svg_data: Dict) -> float:
        """Calculate score for SVG based on geometry and context."""
        score = 0
        
        # Path complexity (most important for wordmarks)
        path_len = geometry.get("totalPathLength", 0)
        path_count = geometry.get("pathCount", 0)
        path_commands = geometry.get("pathCommands", 0)
        
        score += min(path_len / 50, 30)  # Max 30 points from path length
        score += min(path_count * 3, 15)  # Max 15 points from path count
        score += min(path_commands / 5, 15)  # Max 15 points from commands
        
        # Wordmark bonus (wide aspect ratio + complex)
        aspect_ratio = geometry.get("aspectRatio", 1)
        if aspect_ratio > 2:
            score += 20
        elif aspect_ratio > 1.5:
            score += 10
        
        # Penalize square/icon-like
        if 0.8 < aspect_ratio < 1.2:
            score -= 10
        
        # Size bonus
        area = geometry.get("area", 0)
        if area > 2000:
            score += 10
        elif area > 500:
            score += 5
        
        # Position bonus (top-left preferred for logos)
        x = geometry.get("x", 0)
        if x < 300:
            score += 5
        
        # Complexity flag bonus
        if geometry.get("isComplex"):
            score += 5
        
        return max(0, score)
    
    def _calculate_image_score(self, img_data: Dict) -> float:
        """Calculate score for image."""
        score = 20  # Base score
        
        # Logo keyword in alt/class/src
        if img_data.get("isLogoKeyword"):
            score += 30
        
        # Aspect ratio bonus (logos are usually wider)
        aspect = img_data.get("aspectRatio", 1)
        if aspect > 1.5:
            score += 15
        elif aspect > 1.2:
            score += 5
        
        # Size check
        width = img_data.get("width", 0)
        height = img_data.get("height", 0)
        
        if width < 30 or height < 15:
            return 0  # Too small
        
        if 50 < width < 400:
            score += 10
        
        # In header
        if img_data.get("inHeader"):
            score += 10
        
        return score
    
    def _fallback_dom_extraction(self) -> Optional[Dict]:
        """Fallback: Parse DOM directly for logo candidates."""
        
        if not self.soup:
            return None
        
        candidates = []
        
        for a in self.soup.select("header a, nav a, [role='banner'] a, a[href='/']"):
            href = a.get("href", "")
            
            # Check if home link
            if href not in ["/", self.origin, self.origin + "/", "#"]:
                if not href.startswith("/"):
                    continue
            
            text = a.get_text(strip=True)
            if len(text) > 25:
                continue
            
            # Look for SVG
            svg = a.find("svg")
            if svg:
                paths = svg.find_all("path")
                total_d = sum(len(p.get("d", "")) for p in paths)
                
                # Check if repeated
                fp = "".join(p.get("d", "")[:50] for p in paths)[:200]
                if self._is_repeated_svg(fp):
                    continue
                
                candidates.append({
                    "type": "svg",
                    "element": svg,
                    "path_count": len(paths),
                    "path_length": total_d,
                    "score": len(paths) * 5 + total_d / 50
                })
            
            # Look for img
            img = a.find("img")
            if img and img.get("src"):
                alt = (img.get("alt") or "").lower()
                cls = (img.get("class") or [""])
                cls_str = " ".join(cls) if isinstance(cls, list) else cls
                score = 20
                if "logo" in alt or "logo" in cls_str.lower():
                    score += 40
                
                candidates.append({
                    "type": "img",
                    "src": img.get("src"),
                    "alt": alt,
                    "score": score
                })
        
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        if candidates:
            best = candidates[0]
            
            if best["type"] == "svg":
                return {
                    "found": True,
                    "type": "inline_svg",
                    "svg": str(best["element"]),
                    "url": None,
                    "color": None,
                    "confidence": min(0.6, best["score"] / 100),
                    "source": "dom_fallback_svg"
                }
            else:
                return {
                    "found": True,
                    "type": "image",
                    "svg": None,
                    "url": urljoin(self.base_url, best["src"]),
                    "color": None,
                    "confidence": min(0.5, best["score"] / 100),
                    "source": "dom_fallback_img"
                }
        
        return None
    
    def _vision_fallback(self) -> Optional[Dict]:
        """Vision fallback: Detect logo from screenshot using OpenCV."""
        
        if not self.screenshot:
            return None
        
        try:
            import cv2
            import numpy as np
            
            # Decode screenshot
            nparr = np.frombuffer(base64.b64decode(self.screenshot), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None
            
            height, width = img.shape[:2]
            
            # Crop top 20% (header area)
            header_height = int(height * 0.20)
            header_img = img[0:header_height, 0:width]
            
            # Convert to grayscale
            gray = cv2.cvtColor(header_img, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            best_candidate = None
            max_score = 0
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Filter by size
                if w < 40 or h < 20:
                    continue
                if w > width * 0.4:
                    continue
                if h > header_height * 0.8:
                    continue
                
                # Aspect ratio (logos are usually wider)
                aspect = w / float(h)
                if aspect > 8 or aspect < 0.3:
                    continue
                
                # Calculate score
                area = w * h
                
                # Position score (prefer left side)
                center_x = x + w / 2
                pos_score = 1.0 - (center_x / width)  # Higher for left side
                
                # Size score
                size_score = min(area / 5000, 1.0)
                
                # Aspect ratio score (prefer 1.5-4)
                aspect_score = 1.0 if 1.5 < aspect < 4 else 0.5
                
                score = pos_score * 0.3 + size_score * 0.4 + aspect_score * 0.3
                
                if score > max_score:
                    max_score = score
                    best_candidate = (x, y, w, h)
            
            if best_candidate and max_score > 0.3:
                x, y, w, h = best_candidate
                
                # Crop logo region with padding
                pad = 5
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(width, x + w + pad)
                y2 = min(header_height, y + h + pad)
                
                logo_crop = header_img[y1:y2, x1:x2]
                
                # Encode as base64
                _, buffer = cv2.imencode('.png', logo_crop)
                logo_b64 = base64.b64encode(buffer).decode('utf-8')
                
                return {
                    "found": True,
                    "type": "vision_crop",
                    "svg": None,
                    "url": f"data:image/png;base64,{logo_b64}",
                    "color": None,
                    "confidence": round(max_score * 0.5, 2),  # Lower confidence for vision
                    "source": "vision_fallback"
                }
        
        except ImportError:
            logger.warning("OpenCV not available for vision fallback")
        except Exception as e:
            logger.error(f"Vision fallback failed: {e}")
        
        return None
