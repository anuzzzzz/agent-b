import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser import BrowserAgent


def test_basic_navigation():
    """Test basic browser navigation and screenshot"""
    
    print("\n" + "="*60)
    print("PHASE 1 TEST: Basic Browser Automation")
    print("="*60 + "\n")
    
    # Test with context manager
    with BrowserAgent(headless=False) as browser:
        # Navigate to a simple page
        print("\n📋 Test 1: Navigate to Example.com")
        browser.goto("https://example.com")
        
        # Get page title
        title = browser.get_page_title()
        print(f"✅ Page title: {title}")
        assert "Example" in title, "Failed to load example.com"
        
        # Take screenshot
        print("\n📋 Test 2: Take Screenshot")
        screenshot_path = browser.take_screenshot("test_example", task_dir="phase1_test")
        assert screenshot_path.exists(), "Screenshot not saved"
        print(f"✅ Screenshot exists: {screenshot_path}")
        
        # Wait a bit so we can see the browser
        print("\n⏳ Waiting 3 seconds (so you can see the browser)...")
        browser.wait(3000)
    
    print("\n" + "="*60)
    print("✅ PHASE 1 TEST PASSED!")
    print("="*60 + "\n")
    print("Next: Check data/screenshots/phase1_test/ for your screenshot")


def test_asana_homepage():
    """Test navigating to Asana (no login required)"""
    
    print("\n" + "="*60)
    print("BONUS TEST: Navigate to Asana Marketing Page")
    print("="*60 + "\n")
    
    with BrowserAgent(headless=False) as browser:
        # Go to Asana's public homepage
        browser.goto("https://asana.com")
        
        title = browser.get_page_title()
        print(f"✅ Page title: {title}")
        
        screenshot_path = browser.take_screenshot("asana_homepage", task_dir="phase1_test")
        print(f"✅ Screenshot saved: {screenshot_path}")
        
        browser.wait(2000)
    
    print("\n✅ Bonus test passed!\n")


if __name__ == "__main__":
    # Run basic test
    test_basic_navigation()
    
    # Run Asana test
    test_asana_homepage()
    
    print("\n🎉 All Phase 1 tests complete!")
    print("📁 Check: data/screenshots/phase1_test/")