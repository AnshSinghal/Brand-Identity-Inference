import cv2
import numpy as np
import base64
import logging
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

class VisionLogoDetector:
    def __init__(self, screenshot_b64: str):
        self.screenshot_b64 = screenshot_b64

    def detect(self) -> Optional[Dict]:
        """
        Detects a logo in the screenshot using computer vision techniques.
        Returns a dict with 'type', 'data' (base64 extracted crop), and 'confidence'.
        """
        if not self.screenshot_b64:
            return None

        try:
            # 1. Decode base64 to image
            nparr = np.frombuffer(base64.b64decode(self.screenshot_b64), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None

            height, width = img.shape[:2]

            # 2. Crop top 25% (Header area) - where logos usually live
            # We assume logo is in the top header
            header_height = int(height * 0.25)
            header_img = img[0:header_height, 0:width]

            # 3. Preprocessing
            gray = cv2.cvtColor(header_img, cv2.COLOR_BGR2GRAY)
            
            # adaptive thresholding to handle various lighting/contrasts
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)

            # 4. Find Contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            best_candidate = None
            max_score = -1

            # 5. Analyze Contours
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Filter noise
                if w < 20 or h < 10: continue # Too small
                if w > width * 0.5: continue # Too wide (probably a container/nav bar)
                if h > header_height * 0.9: continue # Too tall relative to header

                # Aspect ratio check (Logos are usually 1:1 to 5:1, rarely extremely thin tall/wide)
                aspect_ratio = w / float(h)
                if aspect_ratio > 8 or aspect_ratio < 0.2: continue

                # Position score: Prefer top-left
                # Normalized distance from top-left (0,0)
                # We weight X position heavily because logos are usually on the left or center
                center_x = x + w/2
                center_y = y + h/2
                
                # Normalize positions
                norm_x = center_x / width
                norm_y = center_y / header_height
                
                # Heuristic: 
                # Ideally x is small (left) or middle (center). 
                # y is usually vertically centered in header or specifically top.
                
                # Distance scores (lower is better)
                dist_left = norm_x 
                dist_center = abs(norm_x - 0.5)
                
                # We prefer left slightly more than center, usually
                pos_score = min(dist_left, dist_center) 
                
                # Size score: we want something substantial but not huge
                area = w * h
                target_area = 50 * 50 # 2500 pixels as a baseline logo size
                size_ratio = min(area, target_area) / max(area, target_area)
                
                # Calculate solidity (is it a solid block or scattering?)
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                if hull_area == 0: continue
                solidity = float(area)/hull_area # Rectangular area vs hull area isn't exactly solidity but close for approx
                
                # Combined Score
                # Higher is better
                # - minimize pos_score (distance from ideal spots)
                # - maximize size_score
                
                score = (1.0 - pos_score) * 2 + size_ratio * 1
                
                if score > max_score:
                    max_score = score
                    best_candidate = (x, y, w, h)

            if best_candidate:
                x, y, w, h = best_candidate
                
                # Add a small padding
                pad = 5
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(width, x + w + pad)
                y2 = min(header_height, y + h + pad)
                
                logo_crop = header_img[y1:y2, x1:x2]
                
                # Encode back to base64
                _, buffer = cv2.imencode('.png', logo_crop)
                logo_b64 = base64.b64encode(buffer).decode('utf-8')
                
                return {
                    "found": True,
                    "url": None,
                    "type": "vision_crop",
                    "data": f"data:image/png;base64,{logo_b64}",
                    "confidence": 0.45, # Moderate confidence for fallback
                    "method": "computer_vision_crop"
                }

        except Exception as e:
            logger.error(f"Vision detection failed: {e}")
            return None

        return None
