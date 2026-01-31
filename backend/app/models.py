from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ExtractRequest(BaseModel):
    url: str = Field(..., description="URL to extract design system from")


class ColorInfo(BaseModel):
    color: str
    count: int


class ColorsResult(BaseModel):
    primary: Optional[str] = None
    secondary: Optional[str] = None
    background: Optional[str] = None
    accent: Optional[str] = None
    neutrals: List[str] = []
    all_colors: List[ColorInfo] = []


class FontInfo(BaseModel):
    font: str
    count: int


class TypographyResult(BaseModel):
    heading_font: Optional[str] = None
    body_font: Optional[str] = None
    google_fonts: List[str] = []
    all_fonts: List[FontInfo] = []


class LogoComplexity(BaseModel):
    path_count: Optional[int] = None
    path_length: Optional[int] = None
    aspect_ratio: Optional[float] = None


class LogoResult(BaseModel):
    found: bool = False
    type: Optional[str] = None  # "inline_svg", "image", "svg"
    svg: Optional[str] = None   # Inline SVG HTML
    url: Optional[str] = None   # Image URL (if not inline SVG)
    color: Optional[str] = None # Resolved currentColor
    confidence: Optional[float] = None
    source: Optional[str] = None  # "brand_anchor_svg", "brand_anchor_img", "llm", "none"
    is_wordmark: Optional[bool] = None
    complexity: Optional[LogoComplexity] = None


class VibeResult(BaseModel):
    tone: str = "Unknown"
    audience: str = "Unknown"
    vibe: str = "Unknown"
    analysis: Optional[str] = None
    success: bool = False


class MetaInfo(BaseModel):
    title: str = ""
    description: str = ""
    og_image: Optional[str] = None


class VerificationDebug(BaseModel):
    programmatic: Dict[str, Any] = {}
    llm: Dict[str, Any] = {}
    final: Dict[str, Any] = {}


class DesignSystemResult(BaseModel):
    url: str
    colors: ColorsResult
    typography: TypographyResult
    logo: LogoResult
    vibe: VibeResult
    meta: MetaInfo
    hero_text: str = ""
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    verification: Optional[VerificationDebug] = None
    
    class Config:
        extra = "allow"


class ScanHistoryItem(BaseModel):
    id: str
    url: str
    title: str
    primary_color: Optional[str] = None
    logo_url: Optional[str] = None
    timestamp: datetime


class ScanHistoryList(BaseModel):
    scans: List[ScanHistoryItem] = []
    total: int = 0


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
