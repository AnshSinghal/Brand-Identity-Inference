import re
import cssutils
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import logging
import colorsys

cssutils.log.setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)

HEX_PATTERN = r'#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b'
RGB_PATTERN = r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*[\d.]+)?\s*\)'
HSL_PATTERN = r'hsla?\s*\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%(?:\s*,\s*[\d.]+)?\s*\)'

NEUTRAL_COLORS = {
    "#000000", "#ffffff", "#000", "#fff", 
    "#111111", "#222222", "#333333", "#444444", "#555555",
    "#666666", "#777777", "#888888", "#999999", "#aaaaaa",
    "#bbbbbb", "#cccccc", "#dddddd", "#eeeeee", "#f0f0f0",
    "#f5f5f5", "#fafafa", "transparent", "inherit"
}


def normalize_hex(hex_color: str) -> str:
    if not hex_color or not isinstance(hex_color, str):
        return "#000000"
    hex_color = hex_color.lower().strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c*2 for c in hex_color])
    elif len(hex_color) == 4:
        hex_color = "".join([c*2 for c in hex_color[:3]])
    elif len(hex_color) == 8:
        hex_color = hex_color[:6]
    elif len(hex_color) != 6:
        return "#000000"
    return f"#{hex_color}"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    try:
        hex_color = normalize_hex(hex_color).lstrip("#")
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    except:
        return (0, 0, 0)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def hsl_to_hex(h: float, s: float, l: float) -> str:
    try:
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return rgb_to_hex(int(r * 255), int(g * 255), int(b * 255))
    except:
        return "#000000"


def is_neutral(hex_color: str) -> bool:
    hex_color = normalize_hex(hex_color)
    if hex_color in NEUTRAL_COLORS:
        return True
    r, g, b = hex_to_rgb(hex_color)
    return abs(r - g) < 15 and abs(g - b) < 15 and abs(r - b) < 15


def get_color_saturation(hex_color: str) -> float:
    try:
        r, g, b = hex_to_rgb(hex_color)
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        return s
    except:
        return 0


def get_color_lightness(hex_color: str) -> float:
    try:
        r, g, b = hex_to_rgb(hex_color)
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        return l
    except:
        return 0.5


class ColorExtractor:
    def __init__(self, css_contents: List[str]):
        self.css_contents = css_contents if css_contents else []
        self.context_colors: Dict[str, Dict[str, int]] = {
            "primary": defaultdict(int),
            "secondary": defaultdict(int),
            "background": defaultdict(int),
            "accent": defaultdict(int),
            "neutrals": defaultdict(int),
        }
        self.all_colors: Dict[str, int] = defaultdict(int)
    
    def extract(self) -> Dict:
        for css_text in self.css_contents:
            if css_text:
                self._parse_css(css_text)
        
        result = self._analyze_colors()
        logger.info(f"Extracted colors: primary={result.get('primary')}, total={len(self.all_colors)}")
        return result
    
    def _parse_css(self, css_text: str):
        self._regex_extract(css_text)
        
        try:
            sheet = cssutils.parseString(css_text)
            for rule in sheet:
                if hasattr(rule, 'type') and rule.type == rule.STYLE_RULE:
                    selector = rule.selectorText
                    for prop in rule.style:
                        self._process_property(selector, prop.name, prop.value)
        except:
            pass
    
    def _process_property(self, selector: str, prop_name: str, prop_value: str):
        colors = self._extract_colors_from_value(prop_value)
        for color in colors:
            color = normalize_hex(color)
            self.all_colors[color] += 1
            if is_neutral(color):
                self.context_colors["neutrals"][color] += 1
                continue
            context = self._classify_context(selector, prop_name)
            if context:
                self.context_colors[context][color] += 1
    
    def _extract_colors_from_value(self, value: str) -> List[str]:
        colors = []
        
        for match in re.findall(HEX_PATTERN, value):
            colors.append(normalize_hex(match))
        
        for match in re.findall(RGB_PATTERN, value, re.IGNORECASE):
            try:
                colors.append(rgb_to_hex(int(match[0]), int(match[1]), int(match[2])))
            except:
                pass
        
        for match in re.findall(HSL_PATTERN, value, re.IGNORECASE):
            try:
                colors.append(hsl_to_hex(float(match[0]), float(match[1]), float(match[2])))
            except:
                pass
        
        return colors
    
    def _classify_context(self, selector: str, prop_name: str) -> Optional[str]:
        s, p = selector.lower(), prop_name.lower()
        
        if any(x in s for x in ["button", ".btn", "[type=submit]", ".cta", "submit"]):
            if p in ["background", "background-color", "border-color"]:
                return "primary"
        
        if any(x in s for x in [":link", ":visited", "a:", " a", ".link"]):
            if p == "color":
                return "secondary"
        
        if any(x in s for x in [":hover", ":focus", ":active"]):
            return "accent"
        
        if p in ["background", "background-color"]:
            if any(x in s for x in ["body", "html", ".bg-", "main", ".wrapper", ".container", ":root"]):
                return "background"
            return "primary"
        
        if p == "color":
            if any(x in s for x in ["h1", "h2", ".heading", ".title"]):
                return "secondary"
            return "primary"
        
        if "border" in p:
            return "accent"
        
        return None
    
    def _regex_extract(self, css_text: str):
        for match in re.findall(HEX_PATTERN, css_text):
            color = normalize_hex(match)
            self.all_colors[color] += 1
            if is_neutral(color):
                self.context_colors["neutrals"][color] += 1
            else:
                self.context_colors["primary"][color] += 1
        
        for match in re.findall(RGB_PATTERN, css_text, re.IGNORECASE):
            try:
                color = rgb_to_hex(int(match[0]), int(match[1]), int(match[2]))
                self.all_colors[color] += 1
                if is_neutral(color):
                    self.context_colors["neutrals"][color] += 1
                else:
                    self.context_colors["primary"][color] += 1
            except:
                pass
    
    def _analyze_colors(self) -> Dict:
        result = {
            "primary": None, 
            "secondary": None, 
            "background": None,
            "accent": None, 
            "neutrals": [], 
            "all_colors": []
        }
        
        for context in ["primary", "secondary", "background", "accent"]:
            colors = self.context_colors[context]
            if colors:
                sorted_colors = sorted(colors.items(), key=lambda x: (x[1], get_color_saturation(x[0])), reverse=True)
                best_color = sorted_colors[0][0]
                
                if context == "background":
                    light_colors = [c for c, _ in sorted_colors if get_color_lightness(c) > 0.5]
                    if light_colors:
                        best_color = light_colors[0]
                    else:
                        dark_colors = [c for c, _ in sorted_colors if get_color_lightness(c) < 0.3]
                        if dark_colors:
                            best_color = dark_colors[0]
                
                result[context] = best_color
        
        if not result["primary"]:
            all_non_neutral = {c: f for c, f in self.all_colors.items() if not is_neutral(c)}
            if all_non_neutral:
                sorted_non_neutral = sorted(all_non_neutral.items(), key=lambda x: (x[1], get_color_saturation(x[0])), reverse=True)
                result["primary"] = sorted_non_neutral[0][0]
        
        if not result["background"]:
            result["background"] = "#ffffff"
        
        neutral_sorted = sorted(self.context_colors["neutrals"].items(), key=lambda x: x[1], reverse=True)
        result["neutrals"] = [c for c, _ in neutral_sorted[:5]]
        
        all_sorted = sorted(self.all_colors.items(), key=lambda x: x[1], reverse=True)
        result["all_colors"] = [{"color": c, "count": f} for c, f in all_sorted[:20]]
        
        return result
