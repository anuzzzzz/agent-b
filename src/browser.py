"""Browser agent with persistent session support - solves OAuth/Google login issues"""
from playwright.sync_api import sync_playwright, Browser, Page, Playwright, BrowserContext
from pathlib import Path
from typing import Optional, Dict, Any
import time
from .state_detector import StateDetector
from .config import HEADLESS, BROWSER_TIMEOUT, SCREENSHOTS_DIR


class PersistentBrowserAgent:
    """
    Browser automation with persistent session storage.
    This solves the OAuth/Google login problem by keeping sessions between runs.
    """

    def __init__(self, headless: bool = HEADLESS, session_name: str = "default"):
        """
        Initialize browser with persistent context

        Args:
            headless: Run browser in headless mode
            session_name: Name for the session (allows multiple persistent contexts)
        """
        self.headless = headless
        self.session_name = session_name
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Create session directory
        self.session_dir = Path(f"./browser_sessions/{session_name}")
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _cleanup_stale_locks(self):
        """Remove stale lock files from crashed browser sessions"""
        import subprocess

        lock_file = self.session_dir / "Default" / "LOCK"
        singleton_lock = self.session_dir / "SingletonLock"

        for lock in [lock_file, singleton_lock]:
            if lock.exists():
                # Check if any process is actually using this lock
                try:
                    result = subprocess.run(
                        ["lsof", str(lock)],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode != 0:  # No process using the lock
                        print(f"   🧹 Removing stale lock: {lock.name}")
                        lock.unlink()
                except:
                    # If lsof fails or times out, just remove the lock
                    try:
                        lock.unlink()
                    except:
                        pass

    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"   ⚠️  Exception occurred in context: {exc_type.__name__}: {exc_val}")
        self.close()
        return False  # Don't suppress exceptions

    def start(self):
        """Initialize browser with persistent context"""
        print(f"🚀 Starting browser with session: {self.session_name}")
        self.playwright = sync_playwright().start()

        # Clean up stale lock files from crashed sessions
        self._cleanup_stale_locks()

        # Launch with persistent context - THIS IS THE KEY!
        # It saves cookies, localStorage, and sessions
        try:
            print(f"   Launching persistent context with session dir: {self.session_dir}")
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_dir),
                headless=self.headless,
                # Larger viewport for better web app compatibility
                viewport={'width': 1920, 'height': 1200},
                # Set device scale factor for retina/high-DPI displays
                device_scale_factor=1,
                # Removed problematic settings that may cause crashes
                slow_mo=50,  # Add slight delay to help with stability
            )
            print(f"   ✅ Persistent context launched successfully")
        except Exception as e:
            print(f"   ⚠️  Failed to launch persistent context: {e}")
            print(f"   Retrying with minimal settings...")
            # Fallback: Try with absolute minimal settings
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_dir),
                headless=self.headless,
            )
        
        # Get the first page or create new one
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
            
        self.page.set_default_timeout(BROWSER_TIMEOUT)
        print(f"✅ Browser started with persistent session!")
        
    def is_logged_in(self, app: str) -> bool:
        """
        Check if already logged into an app
        
        Args:
            app: App name to check
            
        Returns:
            True if logged in
        """
        app_checks = {
            'asana': lambda: 'app.asana.com' in self.page.url and '/login' not in self.page.url,
            'linear': lambda: 'linear.app' in self.page.url and '/login' not in self.page.url,
            'notion': lambda: 'notion.so' in self.page.url and '/login' not in self.page.url,
            'github': lambda: 'github.com' in self.page.url and '/login' not in self.page.url,
        }
        
        checker = app_checks.get(app.lower())
        if checker:
            try:
                return checker()
            except:
                return False
        return False

    def manual_login_helper(self, app: str):
        """
        Helper for manual login - keeps browser open for user to login
        
        Args:
            app: App to login to
        """
        login_urls = {
            'asana': 'https://app.asana.com/-/login',
            'linear': 'https://linear.app/login', 
            'notion': 'https://www.notion.so/login',
            'github': 'https://github.com/login',
            'trello': 'https://trello.com/login',
        }
        
        url = login_urls.get(app.lower(), f"https://{app.lower()}.com/login")
        
        print(f"\n{'='*60}")
        print(f"📋 MANUAL LOGIN REQUIRED for {app}")
        print(f"{'='*60}")
        print(f"1. The browser will open {app}'s login page")
        print(f"2. Please login manually (including Google OAuth)")
        print(f"3. Once logged in, press Enter here to continue")
        print(f"4. The session will be saved for future runs!")
        print(f"{'='*60}\n")
        
        self.goto(url)
        
        # Wait for user to complete login
        input(f"Press Enter after you've logged into {app}...")
        
        # Save the session
        self.context.storage_state(path=str(self.session_dir / f"{app}_auth.json"))
        print(f"✅ Session saved for {app}!")
        
    def goto(self, url: str):
        """Navigate to URL"""
        print(f"🌐 Navigating to: {url}")
        self.page.goto(url)
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            self.page.wait_for_load_state("domcontentloaded")
        print("✅ Page loaded!")

    def take_screenshot(self, name: str, task_dir: Optional[Path] = None) -> Path:
        """
        Take a screenshot and save it

        Uses viewport-sized screenshots instead of full_page to avoid layout issues
        and ensure consistent capture area for the LLM
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
        # Use full_page=False for consistent viewport capture
        # This avoids oddly shaped screenshots and matches what user sees
        self.page.screenshot(path=str(filepath), full_page=False)
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
        """Close browser but keep session"""
        if self.context:
            print("🔚 Closing browser (session preserved)...")
            # Save state before closing
            self.context.storage_state(path=str(self.session_dir / "state.json"))
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ Browser closed! Session saved for next run.")

    def get_page_title(self) -> str:
        """Get current page title"""
        return self.page.title()
    
    def get_state_detector(self) -> StateDetector:
        """Get a state detector for this page"""
        return StateDetector(self.page)

    def dismiss_promotional_modals(self) -> bool:
        """
        Attempt to dismiss promotional/onboarding modals that block interaction.

        These are NOT critical modals (like confirmations), but rather:
        - Product tours
        - Feature announcements
        - Promotional popups
        - Cookie notices

        Returns:
            True if a modal was dismissed, False otherwise
        """
        try:
            dismissed = self.page.evaluate("""
                () => {
                    // Common patterns for close buttons in promotional modals
                    const closeSelectors = [
                        '[aria-label*="close" i]',
                        '[aria-label*="dismiss" i]',
                        '[data-testid*="close"]',
                        '[data-testid*="dismiss"]',
                        'button[class*="close"]',
                        'button[class*="dismiss"]',
                        '.modal button:has-text("×")',
                        '.modal button:has-text("Close")',
                        '[role="dialog"] button[aria-label*="close" i]',
                        // Notion-specific patterns
                        '[class*="notion"] button:has-text("×")',
                        '[class*="notion"] [aria-label*="close" i]',
                    ];

                    for (const selector of closeSelectors) {
                        try {
                            const buttons = document.querySelectorAll(selector);
                            for (const btn of buttons) {
                                const style = window.getComputedStyle(btn);
                                if (style.display !== 'none' && style.visibility !== 'hidden') {
                                    // Check if button is in a modal/overlay
                                    let parent = btn.parentElement;
                                    let inModal = false;
                                    for (let i = 0; i < 10 && parent; i++) {
                                        const classes = parent.className?.toLowerCase() || '';
                                        const role = parent.getAttribute('role');
                                        if (classes.includes('modal') ||
                                            classes.includes('dialog') ||
                                            classes.includes('overlay') ||
                                            classes.includes('popup') ||
                                            role === 'dialog') {
                                            inModal = true;
                                            break;
                                        }
                                        parent = parent.parentElement;
                                    }

                                    if (inModal) {
                                        btn.click();
                                        return true;
                                    }
                                }
                            }
                        } catch (e) {
                            // Selector might not be valid, continue
                        }
                    }
                    return false;
                }
            """)

            if dismissed:
                print("   ✓ Dismissed promotional modal")
                self.wait(1000)  # Wait for modal to close
                return True
            return False

        except Exception as e:
            print(f"   ⚠️  Modal dismissal attempt failed: {e}")
            return False

    def find_element_by_visual_description(self, target_text: str, target_description: str = "") -> Optional[str]:
        """
        Find an element using visual description and text matching.

        This is Phase 2 of visual-first navigation: resolve LLM's visual description
        to an actual Playwright locator.

        Args:
            target_text: The visible text the LLM saw (e.g., "Projects", "Create")
            target_description: Optional description (e.g., "button", "link in sidebar")

        Returns:
            Playwright-compatible locator string, or None if not found
        """
        print(f"   🔍 Searching for element with text: '{target_text}'")

        # Strategy 1: Try exact text match with getByText (most reliable for SPAs)
        try:
            locator = self.page.get_by_text(target_text, exact=True)
            if locator.count() > 0 and locator.first.is_visible():
                print(f"   ✓ Found by exact text")
                return f'text="{target_text}"'
        except:
            pass

        # Strategy 2: Try partial text match
        try:
            locator = self.page.get_by_text(target_text, exact=False)
            if locator.count() > 0:
                # If multiple matches, try to use description to disambiguate
                visible_count = sum(1 for i in range(locator.count()) if locator.nth(i).is_visible())
                if visible_count == 1:
                    print(f"   ✓ Found by partial text (1 visible match)")
                    return f'text="{target_text}"'
                elif visible_count > 1:
                    print(f"   ⚠️  Multiple matches ({visible_count}), using first visible")
                    return f'text="{target_text}"'
        except:
            pass

        # Strategy 3: Try role-based matching with text
        if "button" in target_description.lower():
            try:
                locator = self.page.get_by_role("button", name=target_text)
                if locator.count() > 0 and locator.first.is_visible():
                    print(f"   ✓ Found button by role")
                    return f'role=button[name="{target_text}"]'
            except:
                pass

        if "link" in target_description.lower():
            try:
                locator = self.page.get_by_role("link", name=target_text)
                if locator.count() > 0 and locator.first.is_visible():
                    print(f"   ✓ Found link by role")
                    return f'role=link[name="{target_text}"]'
            except:
                pass

        # Strategy 4: Try placeholder/label for inputs
        if "input" in target_description.lower() or "field" in target_description.lower():
            try:
                locator = self.page.get_by_placeholder(target_text)
                if locator.count() > 0 and locator.first.is_visible():
                    print(f"   ✓ Found input by placeholder")
                    return f'placeholder="{target_text}"'
            except:
                pass

            try:
                locator = self.page.get_by_label(target_text)
                if locator.count() > 0 and locator.first.is_visible():
                    print(f"   ✓ Found input by label")
                    return f'label="{target_text}"'
            except:
                pass

        print(f"   ✗ Could not find element with text '{target_text}'")
        return None

    def execute_action(self, action: Dict[str, Any], element_mapping: Dict[int, Dict] = None) -> bool:
        """
        Execute action using SET-OF-MARKS (SoM) approach.

        Expects action with element_id and uses element_mapping to find the element.
        Falls back to visual-first approach if element_id not provided.
        """
        action_type = action.get('action')

        try:
            if action_type == 'click':
                # NEW: SoM approach - use element_id from mapping
                element_id = action.get('element_id')

                if element_id and element_mapping and element_id in element_mapping:
                    # SoM: Use element from mapping
                    elem_data = element_mapping[element_id]
                    print(f"Executing: Click element [{element_id}] ({elem_data.get('role', 'element')})")

                    # Try to find element using its data
                    locator_str = None

                    # Strategy 1: Try by text content
                    text = elem_data.get('text', '').strip()
                    if text:
                        try:
                            locator = self.page.get_by_text(text, exact=True)
                            if locator.count() > 0 and locator.first.is_visible():
                                locator_str = f'text="{text}"'
                                print(f"   ✓ Found by text: '{text[:30]}...'")
                        except:
                            pass

                    # Strategy 2: Try by aria-label
                    if not locator_str:
                        aria = elem_data.get('ariaLabel', '').strip()
                        if aria:
                            try:
                                locator = self.page.get_by_label(aria)
                                if locator.count() > 0 and locator.first.is_visible():
                                    locator_str = f'label="{aria}"'
                                    print(f"   ✓ Found by aria-label: '{aria[:30]}...'")
                            except:
                                pass

                    # Strategy 3: Try by role + text
                    if not locator_str:
                        role = elem_data.get('role', '')
                        if role in ['button', 'link'] and text:
                            try:
                                locator = self.page.get_by_role(role, name=text)
                                if locator.count() > 0 and locator.first.is_visible():
                                    locator_str = f'role={role}[name="{text}"]'
                                    print(f"   ✓ Found by role+text: {role} '{text[:30]}...'")
                            except:
                                pass

                    # Strategy 4: Try CSS selector if provided
                    if not locator_str:
                        selector = elem_data.get('selector', '').strip()
                        if selector:
                            try:
                                locator = self.page.locator(selector)
                                if locator.count() > 0 and locator.first.is_visible():
                                    locator_str = selector
                                    print(f"   ✓ Found by selector")
                            except:
                                pass

                    if not locator_str:
                        print(f"   ✗ Could not find element [{element_id}]")
                        return False

                else:
                    # Fallback: Visual-first approach (old method)
                    target_text = action.get('target_text', '')
                    target_description = action.get('target_description', '')
                    print(f"Executing: Click '{target_text}' (fallback mode)")

                    locator_str = self.find_element_by_visual_description(target_text, target_description)
                    if not locator_str:
                        selector = action.get('selector')
                        if selector:
                            print(f"   ⚠️  Falling back to CSS selector: {selector}")
                            locator_str = selector
                        else:
                            print(f"   ✗ Could not find element")
                            return False

                # Click using resolved locator
                try:
                    # Handle different locator types
                    if locator_str.startswith('text='):
                        text_value = locator_str[6:-1]  # Remove 'text="' and '"'
                        element = self.page.get_by_text(text_value).first
                    elif locator_str.startswith('role=button'):
                        name = locator_str.split('name="')[1].rstrip('"]')
                        element = self.page.get_by_role("button", name=name).first
                    elif locator_str.startswith('role=link'):
                        name = locator_str.split('name="')[1].rstrip('"]')
                        element = self.page.get_by_role("link", name=name).first
                    elif locator_str.startswith('label='):
                        label_value = locator_str[7:-1]
                        element = self.page.get_by_label(label_value).first
                    else:
                        element = self.page.locator(locator_str).first

                    # Get state before click for verification
                    detector = self.get_state_detector()
                    before_state = detector.get_dom_snapshot()

                    element.click(timeout=10000)
                    self.wait(1000)

                    # After click, check for new empty contenteditable fields and scroll them into view
                    try:
                        # Find all contenteditable elements
                        all_editables = self.page.locator('[contenteditable]').all()
                        # Filter for empty ones (no text content)
                        empty_fields = [e for e in all_editables if not e.text_content().strip()]
                        if empty_fields:
                            # Scroll the first empty contenteditable into view and focus it
                            empty_fields[0].scroll_into_view_if_needed()
                            empty_fields[0].click()  # Click to focus it
                            print(f"   → Scrolled and focused empty contenteditable field")
                    except Exception as e:
                        print(f"   ⚠️  Failed to scroll new field: {str(e)[:50]}")

                    # Verify the click had an effect
                    after_state = detector.get_dom_snapshot()
                    state_changed = (
                        before_state['url'] != after_state['url'] or
                        before_state['modal_count'] != after_state['modal_count'] or
                        abs(before_state['element_count'] - after_state['element_count']) > 5
                    )

                    if state_changed:
                        print(f"   ✓ Click successful (state changed)")
                        return True
                    else:
                        print(f"   ⚠️  Click executed but no state change detected")
                        # Still return True since click didn't throw error
                        # The LLM will see no progress and try a different approach
                        return True
                except Exception as click_error:
                    print(f"   ✗ Click failed: {str(click_error)[:100]}")
                    return False

            elif action_type == 'fill':
                text = action.get('text', '')
                element_id = action.get('element_id')

                if element_id and element_mapping and element_id in element_mapping:
                    # SoM: Use element from mapping
                    elem_data = element_mapping[element_id]
                    print(f"Executing: Fill element [{element_id}] with '{text}'")

                    locator_str = None

                    # Strategy 1: Try by placeholder
                    placeholder = elem_data.get('ariaLabel', '').strip()
                    if placeholder:
                        try:
                            locator = self.page.get_by_placeholder(placeholder)
                            if locator.count() > 0 and locator.first.is_visible():
                                locator_str = f'placeholder="{placeholder}"'
                                print(f"   ✓ Found by placeholder")
                        except:
                            pass

                    # Strategy 2: Try by label
                    if not locator_str and placeholder:
                        try:
                            locator = self.page.get_by_label(placeholder)
                            if locator.count() > 0 and locator.first.is_visible():
                                locator_str = f'label="{placeholder}"'
                                print(f"   ✓ Found by label")
                        except:
                            pass

                    # Strategy 3: Try by text content
                    if not locator_str:
                        elem_text = elem_data.get('text', '').strip()
                        if elem_text:
                            try:
                                locator = self.page.get_by_text(elem_text, exact=True)
                                if locator.count() > 0 and locator.first.is_visible():
                                    locator_str = f'text="{elem_text}"'
                                    print(f"   ✓ Found by text")
                            except:
                                pass

                    # Strategy 4: Try CSS selector
                    if not locator_str:
                        selector = elem_data.get('selector', '').strip()
                        if selector:
                            try:
                                locator = self.page.locator(selector)
                                if locator.count() > 0 and locator.first.is_visible():
                                    locator_str = selector
                                    print(f"   ✓ Found by selector")
                            except:
                                pass

                    if not locator_str:
                        print(f"   ✗ Could not find element [{element_id}]")
                        return False

                else:
                    # Fallback: Visual-first approach
                    target_text = action.get('target_text', '')
                    target_description = action.get('target_description', '')
                    print(f"Executing: Fill '{target_text}' with '{text}' (fallback mode)")

                    locator_str = self.find_element_by_visual_description(target_text, target_description)
                    if not locator_str:
                        selector = action.get('selector')
                        if selector:
                            print(f"   ⚠️  Falling back to CSS selector: {selector}")
                            locator_str = selector
                        else:
                            print(f"   ✗ Could not find element")
                            return False

                try:
                    # Handle different locator types
                    if locator_str.startswith('placeholder='):
                        placeholder_value = locator_str[13:-1]
                        element = self.page.get_by_placeholder(placeholder_value).first
                    elif locator_str.startswith('label='):
                        label_value = locator_str[7:-1]
                        element = self.page.get_by_label(label_value).first
                    elif locator_str.startswith('text='):
                        text_value = locator_str[6:-1]
                        element = self.page.get_by_text(text_value).first
                    else:
                        element = self.page.locator(locator_str).first

                    # Special handling: if element isn't fillable, try to find contenteditable child
                    try:
                        # Test if element is fillable
                        is_fillable = element.evaluate('el => el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.hasAttribute("contenteditable")')
                        if not is_fillable:
                            # Try to find contenteditable child
                            contenteditable = element.locator('[contenteditable]').first
                            if contenteditable.count() > 0:
                                element = contenteditable
                                print(f"   → Found contenteditable child")
                    except:
                        pass

                    element.fill(text, timeout=10000)
                    # Store the filled element for potential Enter key press
                    self.last_filled_element = element
                    print(f"   ✓ Fill successful")
                    return True
                except Exception as fill_error:
                    print(f"   ✗ Fill failed: {str(fill_error)[:100]}")
                    return False

            elif action_type == 'press_key':
                key = action.get('key', 'Enter')
                print(f"Executing: Press key '{key}'")
                try:
                    # If Enter and we have a last filled element, press it on that element
                    if key == 'Enter' and hasattr(self, 'last_filled_element') and self.last_filled_element:
                        print(f"   Pressing Enter on last filled element")
                        self.last_filled_element.press(key)
                    else:
                        # Otherwise send to page globally
                        self.page.keyboard.press(key)
                    self.wait(1000)
                    print(f"   ✓ Key press successful")
                    return True
                except Exception as key_error:
                    print(f"   ✗ Key press failed: {str(key_error)[:100]}")
                    return False

            elif action_type == 'wait':
                milliseconds = action.get('milliseconds', 2000)
                print(f"Executing: Wait {milliseconds}ms")
                self.wait(milliseconds)
                return True

            elif action_type == 'screenshot':
                description = action.get('description', 'state')
                print(f"Executing: Screenshot - {description}")
                return True

            elif action_type == 'done':
                print("Executing: Task complete")
                return True

            else:
                print(f"Unknown action type: {action_type}")
                return False

        except Exception as e:
            print(f"Failed to execute action: {e}")
            return False

    def clear_session(self):
        """Clear the saved session for this browser"""
        import shutil
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)
            self.session_dir.mkdir(parents=True, exist_ok=True)
            print(f"🗑️  Session cleared for {self.session_name}")


# Compatibility wrapper to use with existing code
BrowserAgent = PersistentBrowserAgent