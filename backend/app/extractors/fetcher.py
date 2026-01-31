import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import base64
import re
import asyncio
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class WebsiteFetcher:
    """
    Async website fetcher using Playwright Async API.
    Works correctly inside FastAPI's asyncio event loop.
    """
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    # Enhanced JavaScript for SVG geometry and brand anchor extraction
    EXTRACTION_SCRIPT = """
    () => {
        const origin = location.origin;
        const results = {
            brandAnchors: [],
            allSvgs: [],
            headerImages: [],
            allImages: [],
            svgCount: document.querySelectorAll('svg').length
        };
        
        function getAbsUrl(url) {
            try { return new URL(url, document.baseURI).href; } catch(e) { return url; }
        }
        
        function isBrandAnchor(a) {
            const href = a.getAttribute('href') || '';
            if (!href) return false;
            
            const isHomeLink = href === '/' || href === '#' || 
                              href === origin || href === origin + '/' ||
                              (href.startsWith('/') && !href.includes('/') && href.length < 10);
            
            if (!isHomeLink && href.startsWith('http') && !href.includes(origin)) {
                return false;
            }
            
            if (!a.closest('header, nav, [role="banner"], .header, .navbar')) return false;
            
            const text = a.textContent.trim();
            if (text.length > 25) return false;
            
            const hasGraphics = a.querySelector('svg, img, [class*="logo"], [class*="brand"]');
            if (!hasGraphics && text.length > 0) return false;
            
            return true;
        }
        
        function getSvgGeometry(svg) {
            const rect = svg.getBoundingClientRect();
            const paths = svg.querySelectorAll('path');
            const circles = svg.querySelectorAll('circle');
            const rects = svg.querySelectorAll('rect');
            const polygons = svg.querySelectorAll('polygon');
            const texts = svg.querySelectorAll('text');
            
            let totalPathLength = 0;
            let pathCommands = 0;
            let fingerprint = '';
            
            paths.forEach(p => {
                const d = p.getAttribute('d') || '';
                totalPathLength += d.length;
                pathCommands += (d.match(/[MLHVCSQTAZ]/gi) || []).length;
                fingerprint += d;
            });
            
            const viewBox = svg.getAttribute('viewBox') || '';
            const [vbX, vbY, vbW, vbH] = viewBox.split(/\\s+/).map(parseFloat);
            
            return {
                width: rect.width,
                height: rect.height,
                x: rect.x,
                y: rect.y,
                area: rect.width * rect.height,
                aspectRatio: rect.width / Math.max(1, rect.height),
                viewBox: { x: vbX || 0, y: vbY || 0, w: vbW || rect.width, h: vbH || rect.height },
                pathCount: paths.length,
                totalPathLength: totalPathLength,
                pathCommands: pathCommands,
                circleCount: circles.length,
                rectCount: rects.length,
                polygonCount: polygons.length,
                textCount: texts.length,
                totalElements: paths.length + circles.length + rects.length + polygons.length,
                isComplex: totalPathLength > 500 || paths.length > 3,
                isWordmark: rect.width > rect.height * 1.5 && pathCommands > 20,
                fingerprint: fingerprint.substring(0, 200)  // For deduplication
            };
        }
        
        function getComputedColors(el) {
            try {
                const style = window.getComputedStyle(el);
                return {
                    color: style.color,
                    fill: style.fill,
                    backgroundColor: style.backgroundColor
                };
            } catch(e) {
                return {};
            }
        }
        
        function extractSvgData(svg, context = 'page') {
            const geometry = getSvgGeometry(svg);
            const colors = getComputedColors(svg);
            
            if (geometry.width < 10 || geometry.height < 10) return null;
            
            return {
                html: svg.outerHTML,
                geometry: geometry,
                colors: colors,
                context: context,
                id: svg.id || null,
                className: typeof svg.className === 'string' ? svg.className : svg.className.baseVal || '',
                inHeader: !!svg.closest('header, nav, [role="banner"]'),
                isInLink: !!svg.closest('a')
            };
        }
        
        function extractImageData(img, context = 'page') {
            const rect = img.getBoundingClientRect();
            if (rect.width < 20 || rect.height < 10) return null;
            
            const parent = img.closest('a');
            
            return {
                src: img.currentSrc || img.src,
                alt: img.alt || '',
                width: rect.width,
                height: rect.height,
                x: rect.x,
                y: rect.y,
                aspectRatio: rect.width / Math.max(1, rect.height),
                context: context,
                className: img.className || '',
                inHeader: !!img.closest('header, nav, [role="banner"]'),
                isInLink: !!parent,
                linkHref: parent ? parent.getAttribute('href') : null,
                isLogoKeyword: /logo|brand|mark/i.test(img.alt + img.className + img.src)
            };
        }
        
        // === BRAND ANCHOR EXTRACTION ===
        const anchors = document.querySelectorAll('header a, nav a, [role="banner"] a, a[href="/"], a[href="' + origin + '"]');
        
        anchors.forEach(a => {
            if (!isBrandAnchor(a)) return;
            
            const rect = a.getBoundingClientRect();
            const svgs = [];
            const imgs = [];
            
            a.querySelectorAll('svg').forEach(svg => {
                const data = extractSvgData(svg, 'brand_anchor');
                if (data) svgs.push(data);
            });
            
            a.querySelectorAll('img').forEach(img => {
                const data = extractImageData(img, 'brand_anchor');
                if (data) imgs.push(data);
            });
            
            if (svgs.length > 0 || imgs.length > 0) {
                results.brandAnchors.push({
                    href: a.getAttribute('href'),
                    rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
                    ariaLabel: a.getAttribute('aria-label') || '',
                    text: a.textContent.trim().substring(0, 50),
                    svgs: svgs,
                    imgs: imgs
                });
            }
        });
        
        // === ALL SVGs IN HEADER ===
        document.querySelectorAll('header svg, nav svg, [role="banner"] svg').forEach(svg => {
            const data = extractSvgData(svg, 'header');
            if (data && data.geometry.area > 100) {
                results.allSvgs.push(data);
            }
        });
        
        // === ALL IMAGES IN HEADER ===
        document.querySelectorAll('header img, nav img, [role="banner"] img').forEach(img => {
            const data = extractImageData(img, 'header');
            if (data) {
                results.headerImages.push(data);
            }
        });
        
        // === TOP PAGE IMAGES (for fallback) ===
        document.querySelectorAll('img').forEach(img => {
            const data = extractImageData(img, 'page');
            if (data && data.y < 300 && data.isLogoKeyword) {
                results.allImages.push(data);
            }
        });
        
        return results;
    }
    """
    
    def __init__(self, url: str, use_playwright: bool = True):
        self.url = url
        self.use_playwright = use_playwright
        self.html = ""
        self.soup = None
        self.css_contents = []
        self.screenshot = None
        self.extraction_data = {}
        self.origin = urlparse(url).scheme + "://" + urlparse(url).netloc
        
    async def fetch_async(self) -> Dict:
        """Async fetch using Playwright Async API."""
        success = False
        
        if self.use_playwright:
            success = await self._fetch_with_playwright_async()
        
        if not success:
            logger.info("Playwright failed, falling back to requests")
            self._fetch_with_requests()
        
        if self.html:
            self.soup = BeautifulSoup(self.html, "lxml")
            self._extract_css()
        
        # Log SVG count for sanity check
        if self.soup:
            svg_count = len(self.soup.find_all('svg'))
            logger.info(f"Rendered SVG count: {svg_count}")
        
        return {
            "html": self.html,
            "soup": self.soup,
            "css": self.css_contents,
            "base_url": self.url,
            "origin": self.origin,
            "screenshot": self.screenshot,
            "brand_anchors": self.extraction_data.get("brandAnchors", []),
            "all_svgs": self.extraction_data.get("allSvgs", []),
            "header_images": self.extraction_data.get("headerImages", []),
            "all_images": self.extraction_data.get("allImages", []),
            "svg_count": self.extraction_data.get("svgCount", 0)
        }
    
    def fetch(self) -> Dict:
        """Sync wrapper - runs async fetch in new event loop if needed."""
        try:
            loop = asyncio.get_running_loop()
            # We're inside an async context, need to use await
            # This method shouldn't be called from async context
            raise RuntimeError("Use fetch_async() instead when in async context")
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self.fetch_async())
    
    async def _fetch_with_playwright_async(self) -> bool:
        """Fetch using Playwright Async API - works correctly inside FastAPI."""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                page = await browser.new_page(
                    viewport={"width": 1440, "height": 900},
                    user_agent=self.HEADERS["User-Agent"]
                )
                
                # Anti-detection
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                logger.info(f"Navigating to {self.url}")
                await page.goto(self.url, timeout=30000, wait_until="domcontentloaded")
                
                # CRITICAL: Wait for header/nav content, not just networkidle
                try:
                    await page.wait_for_selector(
                        "header svg, nav svg, header img, nav img, [role='banner'] svg",
                        timeout=8000
                    )
                except:
                    logger.debug("No header graphics found via selector, continuing...")
                
                # CRITICAL: DOM stability wait using MutationObserver
                try:
                    await page.evaluate("""
                    () => new Promise(resolve => {
                        let last = Date.now();
                        const obs = new MutationObserver(() => last = Date.now());
                        obs.observe(document.body, {childList: true, subtree: true});
                        const check = () => {
                            if (Date.now() - last > 800) {
                                obs.disconnect();
                                resolve();
                            } else {
                                requestAnimationFrame(check);
                            }
                        };
                        setTimeout(check, 100);
                    })
                    """)
                except Exception as e:
                    logger.debug(f"DOM stabilization error: {e}")
                
                self.html = await page.content()
                
                # Run comprehensive extraction script
                try:
                    self.extraction_data = await page.evaluate(self.EXTRACTION_SCRIPT)
                    logger.info(f"Extracted: {len(self.extraction_data.get('brandAnchors', []))} brand anchors, "
                               f"{len(self.extraction_data.get('allSvgs', []))} SVGs, "
                               f"{len(self.extraction_data.get('headerImages', []))} header images, "
                               f"Total SVGs on page: {self.extraction_data.get('svgCount', 0)}")
                except Exception as e:
                    logger.error(f"Extraction script failed: {e}")
                    self.extraction_data = {}
                
                # Take screenshot for vision fallback
                try:
                    screenshot_bytes = await page.screenshot(clip={"x": 0, "y": 0, "width": 1440, "height": 600})
                    self.screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                except Exception as e:
                    logger.debug(f"Screenshot failed: {e}")
                
                await browser.close()
                return len(self.html) > 500
                
        except Exception as e:
            logger.error(f"Playwright async error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _fetch_with_requests(self):
        """Fallback to simple HTTP request (no JS execution)."""
        try:
            resp = requests.get(self.url, headers=self.HEADERS, timeout=15)
            resp.raise_for_status()
            self.html = resp.text
            logger.warning("Using requests fallback - no JS execution, SVGs may be missing")
        except Exception as e:
            logger.error(f"Requests error: {e}")
            self.html = ""
    
    def _extract_css(self):
        """Extract CSS from inline styles and linked stylesheets."""
        if not self.soup:
            return
            
        for style in self.soup.find_all("style"):
            if style.string:
                self.css_contents.append(style.string)
        
        for link in self.soup.find_all("link", rel="stylesheet")[:3]:
            href = link.get("href")
            if href:
                try:
                    css_url = urljoin(self.url, href)
                    resp = requests.get(css_url, headers=self.HEADERS, timeout=5)
                    if resp.status_code == 200:
                        self.css_contents.append(resp.text[:50000])
                except:
                    pass
    
    def get_meta_info(self) -> Dict:
        """Extract meta information from the page."""
        if not self.soup:
            return {"title": "", "description": "", "og_image": ""}
        
        title = ""
        if self.soup.title and self.soup.title.string:
            title = self.soup.title.string.strip()
        
        description = ""
        meta_desc = self.soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "")
        if not description:
            og_desc = self.soup.find("meta", attrs={"property": "og:description"})
            if og_desc:
                description = og_desc.get("content", "")
        
        og_image = ""
        og_img = self.soup.find("meta", attrs={"property": "og:image"})
        if og_img:
            og_image = og_img.get("content", "")
        
        return {"title": title, "description": description, "og_image": og_image}
    
    def get_hero_text(self) -> str:
        """Extract hero/main text content from the page."""
        if not self.soup:
            return ""
        
        texts = []
        
        h1 = self.soup.find("h1")
        if h1:
            texts.append(h1.get_text(strip=True))
        
        for h2 in self.soup.find_all("h2")[:2]:
            texts.append(h2.get_text(strip=True))
        
        for p in self.soup.find_all("p")[:5]:
            text = p.get_text(strip=True)
            if len(text) > 30:
                texts.append(text[:200])
        
        for cls in ["hero", "banner", "jumbotron", "masthead"]:
            hero = self.soup.find(class_=re.compile(cls, re.I))
            if hero:
                texts.append(hero.get_text(strip=True)[:300])
                break
        
        return " | ".join(texts)[:800]
