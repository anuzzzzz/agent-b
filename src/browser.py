from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from pathlib import Path
from typing import Optional
import time
from .state_detector import StateDetector

from .config import HEADLESS, BROWSER_TIMEOUT, SCREENSHOTS_DIR


class BrowserAgent:
    #browser automation behaviour 


    def __init__(self, headless: bool = HEADLESS):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None


    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    
    def start(self):
        """Initialize browser"""
        print("🚀 Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        self.page.set_default_timeout(BROWSER_TIMEOUT)
        print("✅ Browser started!")

    
    def goto(self, url: str):
        """Navigate to URL"""
        print(f"🌐 Navigating to: {url}")
        self.page.goto(url)
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            # If networkidle times out, wait for domcontentloaded instead
            self.page.wait_for_load_state("domcontentloaded")
        print("✅ Page loaded!")


    def take_screenshot(self, name: str, task_dir: Optional[Path] = None) -> Path:
        """
        Take a screenshot and save it
        
        Args:
            name: Screenshot name (e.g., "01_initial_state")
            task_dir: Optional subdirectory for organizing screenshots
            
        Returns:
            Path to saved screenshot
        """
        if task_dir:
            save_dir = SCREENSHOTS_DIR / task_dir
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = SCREENSHOTS_DIR
            
        timestamp = int(time.time())
        filename = f"{name}_{timestamp}.png"
        filepath = save_dir / filename
        
        print(f"📸 Taking screenshot: {filename}")
        self.page.screenshot(path=str(filepath), full_page=True)
        print(f"✅ Screenshot saved: {filepath}")
        
        return filepath
    
    def click(self, selector: str):
        """Click an element"""
        print(f"🖱️  Clicking: {selector}")
        self.page.click(selector)
        self.page.wait_for_load_state("networkidle")

    def fill(self, selector: str, text: str):
        """Fill a text input"""
        print(f"⌨️  Filling '{selector}' with: {text}")
        self.page.fill(selector, text)

    def wait(self, milliseconds: int = 1000):
        """Wait for a specified time"""
        print(f"⏳ Waiting {milliseconds}ms...")
        self.page.wait_for_timeout(milliseconds)
    
    def close(self):
        """Close browser"""
        if self.browser:
            print("🔚 Closing browser...")
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ Browser closed!")

    def get_page_title(self) -> str:
        """Get current page title"""
        return self.page.title()
    
    def get_state_detector(self) -> StateDetector:
        """Get a state detector for this page"""
        return StateDetector(self.page)


