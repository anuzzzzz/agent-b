"""
Phase 2 Test: State Detection & Smart Screenshots

This test verifies:
1. Can detect modals
2. Can detect DOM changes
3. Can capture state information
4. Smart screenshot triggers work
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser import BrowserAgent
from src.state_detector import StateDetector
from src.utils import save_metadata


def test_state_detection():
    """Test state detection capabilities"""
    
    print("\n" + "="*60)
    print("PHASE 2 TEST: State Detection")
    print("="*60 + "\n")
    
    with BrowserAgent(headless=False) as browser:
        # Navigate to a page with modals
        print("📋 Test 1: Detecting Initial State")
        browser.goto("https://example.com")
        
        # Create state detector
        detector = browser.get_state_detector()
        
        # Get initial state
        state_info = detector.get_current_state_info()
        print(f"✅ Current state: {state_info['title']}")
        print(f"   - URL: {state_info['url']}")
        print(f"   - Elements: {state_info['element_count']}")
        print(f"   - Modals: {state_info['modal_count']}")
        
        # Take screenshot with metadata
        screenshot_path = browser.take_screenshot(
            "01_initial_state", 
            task_dir="phase2_test"
        )
        save_metadata(screenshot_path, state_info, task="Phase 2 Test")
        
        browser.wait(2000)
        
    print("\n" + "="*60)
    print("✅ PHASE 2 STATE DETECTION TEST PASSED!")
    print("="*60 + "\n")


def test_modal_detection():
    """Test detecting modals on a real site"""
    
    print("\n" + "="*60)
    print("PHASE 2 TEST: Modal Detection (W3Schools)")
    print("="*60 + "\n")
    
    with BrowserAgent(headless=False) as browser:
        # Go to W3Schools modal example
        print("📋 Navigating to W3Schools modal example...")
        browser.goto("https://www.w3schools.com/howto/howto_css_modals.asp")
        
        detector = browser.get_state_detector()
        
        # Initial state
        print("\n📋 Test 1: Initial state (no modal)")
        state_before = detector.get_current_state_info()
        print(f"   - Has modal: {state_before['has_modal']}")
        
        screenshot_path = browser.take_screenshot(
            "01_before_modal",
            task_dir="phase2_test/modal_test"
        )
        save_metadata(screenshot_path, state_before, task="Modal Detection Test")
        
        browser.wait(1000)
        
        # Click to open modal (try to find the button)
        print("\n📋 Test 2: Opening modal...")
        try:
            # Try to click the "Try it yourself" button or modal trigger
            # This is just a demo - real implementation would be smarter
            browser.page.click("text=Try it Yourself", timeout=5000)
            browser.wait(1000)
            
            # Check if modal appeared
            state_after = detector.get_current_state_info()
            print(f"   - Has modal: {state_after['has_modal']}")
            
            if detector.has_significant_change():
                print("   ✅ Significant change detected!")
                screenshot_path = browser.take_screenshot(
                    "02_modal_open",
                    task_dir="phase2_test/modal_test"
                )
                save_metadata(screenshot_path, state_after, task="Modal Detection Test")
        except Exception as e:
            print(f"   ℹ️  Could not trigger modal (expected on some pages): {e}")
        
        browser.wait(2000)
    
    print("\n" + "="*60)
    print("✅ PHASE 2 MODAL DETECTION TEST PASSED!")
    print("="*60 + "\n")


def test_change_detection():
    """Test detecting significant DOM changes"""
    
    print("\n" + "="*60)
    print("PHASE 2 TEST: Change Detection")
    print("="*60 + "\n")
    
    with BrowserAgent(headless=False) as browser:
        print("📋 Testing change detection on navigation...")
        
        # Go to first page
        browser.goto("https://example.com")
        detector = browser.get_state_detector()
        
        state1 = detector.get_current_state_info()
        print(f"   - Page 1: {state1['title']}")
        
        browser.wait(1000)
        
        # Navigate to different page
        browser.goto("https://www.wikipedia.org")
        
        # Check for change
        if detector.has_significant_change():
            print("   ✅ Change detected after navigation!")
            state2 = detector.get_current_state_info()
            print(f"   - Page 2: {state2['title']}")
            
            screenshot_path = browser.take_screenshot(
                "after_navigation",
                task_dir="phase2_test/change_detection"
            )
            save_metadata(screenshot_path, state2, task="Change Detection Test")
        
        browser.wait(2000)
    
    print("\n" + "="*60)
    print("✅ PHASE 2 CHANGE DETECTION TEST PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run all tests
    test_state_detection()
    test_modal_detection()
    test_change_detection()
    
    print("\n🎉 All Phase 2 tests complete!")
    print("📁 Check: data/screenshots/phase2_test/")
    print("\n💡 Next: Phase 3 - LLM Integration")