import re
import cssutils
from collections import defaultdict
from typing import Dict, List, Set
import logging

cssutils.log.setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)

SYSTEM_FONTS = {
    "system-ui", "-apple-system", "blinkmacsystemfont", "segoe ui",
    "roboto", "helvetica", "arial", "sans-serif", "serif", "monospace",
    "helvetica neue", "times new roman", "times", "georgia", "courier",
    "courier new", "lucida console", "lucida sans", "verdana", "tahoma",
    "trebuchet ms", "impact", "comic sans ms", "ui-sans-serif", "ui-serif",
    "ui-monospace", "inherit", "initial", "unset", "revert"
}

ICON_FONTS = {
    "fontawesome", "font awesome", "material icons", "material-icons",
    "ionicons", "glyphicons", "icomoon", "feather", "webflow-icons",
    "icon", "icons", "fa", "fas", "far", "fab"
}

GOOGLE_FONTS_PATTERN = r'fonts\.googleapis\.com/css2?\?family=([^&"\'\)]+)'


class TypographyExtractor:
    def __init__(self, css_contents: List[str], html: str = ""):
        self.css_contents = css_contents
        self.html = html
        self.heading_fonts: Dict[str, int] = defaultdict(int)
        self.body_fonts: Dict[str, int] = defaultdict(int)
        self.google_fonts: Set[str] = set()
        self.all_fonts: Dict[str, int] = defaultdict(int)
    
    def extract(self) -> Dict:
        self._extract_google_fonts()
        for css_text in self.css_contents:
            self._parse_css(css_text)
        return self._analyze_fonts()
    
    def _extract_google_fonts(self):
        if not self.html:
            return
        matches = re.findall(GOOGLE_FONTS_PATTERN, self.html)
        for match in matches:
            decoded = match.replace("+", " ").replace("%20", " ")
            fonts = re.findall(r'([A-Za-z\s]+)(?::|;|$)', decoded)
            for font in fonts:
                font = font.strip()
                if font:
                    self.google_fonts.add(font)
    
    def _parse_css(self, css_text: str):
        try:
            sheet = cssutils.parseString(css_text)
            for rule in sheet:
                if hasattr(rule, 'type') and rule.type == rule.STYLE_RULE:
                    selector = rule.selectorText
                    for prop in rule.style:
                        if prop.name == "font-family":
                            self._process_font_family(selector, prop.value)
                        elif prop.name == "font":
                            self._process_font_shorthand(selector, prop.value)
        except:
            self._regex_extract(css_text)
    
    def _process_font_family(self, selector: str, value: str):
        fonts = self._parse_font_list(value)
        for font in fonts:
            font_lower = font.lower()
            if font_lower in SYSTEM_FONTS:
                continue
            if font_lower in ICON_FONTS or any(icon in font_lower for icon in ICON_FONTS):
                continue
            if font.startswith("var("):
                continue
            self.all_fonts[font] += 1
            context = self._classify_selector(selector)
            if context == "heading":
                self.heading_fonts[font] += 1
            elif context == "body":
                self.body_fonts[font] += 1
    
    def _process_font_shorthand(self, selector: str, value: str):
        parts = value.split(",")
        if parts:
            first_part = parts[0].strip()
            size_match = re.search(r'(\d+(?:px|em|rem|pt|%))\s+(.+)', first_part)
            if size_match:
                font_name = size_match.group(2).strip().strip('"\'')
                self._process_font_family(selector, font_name + "," + ",".join(parts[1:]))
    
    def _parse_font_list(self, value: str) -> List[str]:
        fonts = []
        parts = re.split(r',\s*', value)
        for part in parts:
            font = part.strip().strip('"\'')
            if font:
                fonts.append(font)
        return fonts
    
    def _classify_selector(self, selector: str) -> str:
        s = selector.lower()
        if any(x in s for x in ["h1", "h2", "h3", "h4", "h5", "h6", ".heading", ".title", ".headline"]):
            return "heading"
        if any(x in s for x in ["body", "p", ".text", ".content", ".paragraph", "html"]):
            return "body"
        return "body"
    
    def _regex_extract(self, css_text: str):
        pattern = r'font-family\s*:\s*([^;]+)'
        matches = re.findall(pattern, css_text, re.IGNORECASE)
        for match in matches:
            fonts = self._parse_font_list(match)
            for font in fonts:
                if font.lower() not in SYSTEM_FONTS and not font.startswith("var("):
                    self.all_fonts[font] += 1
    
    def _analyze_fonts(self) -> Dict:
        result = {"heading_font": None, "body_font": None, "google_fonts": list(self.google_fonts), "all_fonts": []}
        
        filtered_fonts = {
            f: c for f, c in self.all_fonts.items() 
            if f.lower() not in SYSTEM_FONTS and f.lower() not in ICON_FONTS
            and not any(icon in f.lower() for icon in ICON_FONTS) and not f.startswith("var(")
        }
        
        if self.heading_fonts:
            result["heading_font"] = max(self.heading_fonts.items(), key=lambda x: x[1])[0]
        
        if self.body_fonts:
            result["body_font"] = max(self.body_fonts.items(), key=lambda x: x[1])[0]
        
        if not result["heading_font"] or not result["body_font"]:
            sorted_all = sorted(filtered_fonts.items(), key=lambda x: x[1], reverse=True)
            if sorted_all:
                if not result["heading_font"]:
                    result["heading_font"] = sorted_all[0][0]
                if not result["body_font"] and len(sorted_all) > 1:
                    result["body_font"] = sorted_all[1][0]
                elif not result["body_font"]:
                    result["body_font"] = sorted_all[0][0]
        
        if not result["heading_font"] and self.google_fonts:
            result["heading_font"] = list(self.google_fonts)[0]
        if not result["body_font"] and self.google_fonts:
            fonts_list = list(self.google_fonts)
            result["body_font"] = fonts_list[1] if len(fonts_list) > 1 else fonts_list[0]
        
        sorted_fonts = sorted(filtered_fonts.items(), key=lambda x: x[1], reverse=True)
        result["all_fonts"] = [{"font": f, "count": c} for f, c in sorted_fonts[:10]]
        
        return result
