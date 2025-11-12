"""Authentication manager for handling login flows across different apps"""
import os
from typing import Dict, Optional, Any
from pathlib import Path
import json
from dotenv import load_dotenv

from playwright.sync_api import Page
from .browser import BrowserAgent

load_dotenv()


class AuthManager:
    """Handle authentication for different web applications"""
    
    def __init__(self, credentials_path: Optional[Path] = None):
        """
        Initialize auth manager
        
        Args:
            credentials_path: Optional path to credentials JSON file
        """
        self.credentials_path = credentials_path
        self.credentials = self._load_credentials()
        
        # Auth configurations for different apps
        self.auth_configs = {
            'linear': {
                'login_url': 'https://linear.app/login',
                'needs_workspace': True,
                'selectors': {
                    'email': 'input[name="email"], input[type="email"]',
                    'password': 'input[name="password"], input[type="password"]',
                    'submit': 'button[type="submit"], button:has-text("Continue"), button:has-text("Sign in")',
                    'workspace': 'input[placeholder*="workspace"]',
                }
            },
            'notion': {
                'login_url': 'https://www.notion.so/login',
                'needs_workspace': False,
                'selectors': {
                    'email': 'input[type="email"], input[placeholder*="email"]',
                    'password': 'input[type="password"]',
                    'submit': 'button[type="submit"], div[role="button"]:has-text("Continue")',
                    'continue_with_email': 'div:has-text("Continue with email")',
                }
            },
            'asana': {
                'login_url': 'https://app.asana.com/-/login',
                'needs_workspace': False,
                'selectors': {
                    'email': 'input[type="email"], input[name="email"]',
                    'password': 'input[type="password"], input[name="password"]',
                    'submit': 'div[role="button"]:has-text("Log in"), button:has-text("Log in")',
                    'continue': 'div[role="button"]:has-text("Continue")',
                }
            },
            'github': {
                'login_url': 'https://github.com/login',
                'needs_workspace': False,
                'selectors': {
                    'email': 'input[name="login"]',
                    'password': 'input[name="password"]',
                    'submit': 'input[type="submit"]',
                }
            }
        }
    
    def _load_credentials(self) -> Dict[str, Dict[str, str]]:
        """Load credentials from environment or file"""
        credentials = {}
        
        # Try to load from environment variables first
        for app in ['linear', 'notion', 'asana', 'github']:
            app_upper = app.upper()
            email = os.getenv(f"{app_upper}_EMAIL")
            password = os.getenv(f"{app_upper}_PASSWORD")
            workspace = os.getenv(f"{app_upper}_WORKSPACE")
            
            if email and password:
                credentials[app] = {
                    'email': email,
                    'password': password,
                }
                if workspace:
                    credentials[app]['workspace'] = workspace
        
        # Load from file if provided
        if self.credentials_path and self.credentials_path.exists():
            with open(self.credentials_path, 'r') as f:
                file_creds = json.load(f)
                credentials.update(file_creds)
        
        return credentials
    
    def has_credentials(self, app: str) -> bool:
        """Check if we have credentials for an app"""
        return app.lower() in self.credentials
    
    def requires_auth(self, browser: BrowserAgent, app: str) -> bool:
        """
        Check if the current page requires authentication

        Args:
            browser: Browser instance
            app: App name

        Returns:
            True if login is required
        """
        current_url = browser.page.url

        # App-specific authentication detection
        app = app.lower()

        if app == 'asana':
            # Asana: check if we're on login page or workspace selection
            if '-/login' in current_url or 'auth' in current_url:
                return True
            # Check if we can see the main app interface
            try:
                # Look for Asana's main topbar (indicates logged in)
                topbar = browser.page.locator('div[class*="TopbarStructure"], div[class*="Topbar"]').first
                if topbar.is_visible(timeout=2000):
                    return False  # Already logged in
            except:
                pass

        elif app == 'linear':
            # Linear: check URL and main navigation
            if '/login' in current_url or 'auth' in current_url:
                return True
            try:
                nav = browser.page.locator('nav[class*="navigation"]').first
                if nav.is_visible(timeout=2000):
                    return False
            except:
                pass

        elif app == 'notion':
            # Notion: check URL and sidebar
            if '/login' in current_url or 'auth' in current_url:
                return True
            try:
                sidebar = browser.page.locator('div[class*="sidebar"]').first
                if sidebar.is_visible(timeout=2000):
                    return False
            except:
                pass

        # Generic checks - only if app-specific checks didn't determine
        # Check URL for explicit login paths
        login_url_patterns = ['/login', '/signin', '/auth/login', '/-/login']
        if any(pattern in current_url.lower() for pattern in login_url_patterns):
            return True

        # Check page title for login indicators
        title = browser.page.title().lower()
        if title.startswith('log in') or title.startswith('sign in'):
            return True

        # Check for visible password fields (strong indicator, but be careful)
        try:
            password_field = browser.page.locator('input[type="password"]').first
            if password_field.is_visible(timeout=1000):
                # Make sure it's actually a login form, not a settings page
                page_text = browser.page.locator('body').inner_text().lower()
                if 'log in' in page_text or 'sign in' in page_text:
                    return True
        except:
            pass

        return False
    
    def login(self, browser: BrowserAgent, app: str) -> bool:
        """
        Perform login for specified app
        
        Args:
            browser: Browser instance
            app: App name
            
        Returns:
            True if login successful
        """
        app = app.lower()
        
        if not self.has_credentials(app):
            print(f"⚠️  No credentials found for {app}")
            print(f"   Set environment variables: {app.upper()}_EMAIL and {app.upper()}_PASSWORD")
            return False
        
        if app not in self.auth_configs:
            print(f"⚠️  No auth configuration for {app}")
            return False
        
        config = self.auth_configs[app]
        creds = self.credentials[app]
        
        print(f"🔐 Attempting login for {app}...")
        
        try:
            # Navigate to login page if needed
            if not self.requires_auth(browser, app):
                browser.goto(config['login_url'])
                browser.wait(3000)
            
            # App-specific login flows
            if app == 'notion':
                return self._login_notion(browser, config, creds)
            elif app == 'linear':
                return self._login_linear(browser, config, creds)
            elif app == 'asana':
                return self._login_asana(browser, config, creds)
            else:
                # Generic login flow
                return self._generic_login(browser, config, creds)
                
        except Exception as e:
            print(f"❌ Login failed for {app}: {e}")
            return False
    
    def _generic_login(self, browser: BrowserAgent, config: Dict, creds: Dict) -> bool:
        """Generic login flow that works for most apps"""
        try:
            # Fill email
            print("   Entering email...")
            email_field = browser.page.locator(config['selectors']['email']).first
            email_field.fill(creds['email'])
            browser.wait(500)
            
            # Fill password
            print("   Entering password...")
            password_field = browser.page.locator(config['selectors']['password']).first
            password_field.fill(creds['password'])
            browser.wait(500)
            
            # Submit
            print("   Submitting...")
            submit_button = browser.page.locator(config['selectors']['submit']).first
            submit_button.click()
            
            # Wait for navigation
            browser.wait(5000)
            
            # Check if login succeeded
            if not self.requires_auth(browser, 'generic'):
                print("✅ Login successful!")
                return True
            else:
                print("⚠️  Still on login page, login may have failed")
                return False
                
        except Exception as e:
            print(f"   Error during login: {e}")
            return False
    
    def _login_notion(self, browser: BrowserAgent, config: Dict, creds: Dict) -> bool:
        """Notion-specific login flow"""
        try:
            # Notion often has "Continue with email" button first
            try:
                email_button = browser.page.locator(config['selectors']['continue_with_email']).first
                if email_button.is_visible():
                    email_button.click()
                    browser.wait(2000)
            except:
                pass
            
            # Enter email
            print("   Entering email...")
            email_field = browser.page.locator(config['selectors']['email']).first
            email_field.fill(creds['email'])
            browser.wait(1000)
            
            # Click continue
            continue_btn = browser.page.locator('button:has-text("Continue"), div[role="button"]:has-text("Continue")').first
            continue_btn.click()
            browser.wait(3000)
            
            # Enter password
            print("   Entering password...")
            password_field = browser.page.locator(config['selectors']['password']).first
            password_field.fill(creds['password'])
            browser.wait(1000)
            
            # Submit
            print("   Submitting...")
            submit_button = browser.page.locator('button:has-text("Continue"), div[role="button"]:has-text("Continue")').first
            submit_button.click()
            
            # Wait for navigation
            browser.wait(7000)
            
            print("✅ Notion login successful!")
            return True
            
        except Exception as e:
            print(f"   Notion login error: {e}")
            return False
    
    def _login_linear(self, browser: BrowserAgent, config: Dict, creds: Dict) -> bool:
        """Linear-specific login flow"""
        try:
            # Linear might need workspace URL
            if 'workspace' in creds:
                workspace_url = f"https://linear.app/{creds['workspace']}"
                browser.goto(workspace_url)
                browser.wait(3000)
            
            # Check if we need to enter workspace
            try:
                workspace_field = browser.page.locator(config['selectors']['workspace']).first
                if workspace_field.is_visible() and 'workspace' in creds:
                    workspace_field.fill(creds['workspace'])
                    browser.wait(1000)
                    # Submit workspace
                    browser.page.keyboard.press('Enter')
                    browser.wait(3000)
            except:
                pass
            
            # Standard email/password flow
            return self._generic_login(browser, config, creds)
            
        except Exception as e:
            print(f"   Linear login error: {e}")
            return False
    
    def _login_asana(self, browser: BrowserAgent, config: Dict, creds: Dict) -> bool:
        """Asana-specific login flow"""
        try:
            # Enter email
            print("   Entering email...")
            email_field = browser.page.locator(config['selectors']['email']).first
            email_field.fill(creds['email'])
            browser.wait(1000)
            
            # Click continue (Asana has a two-step process)
            try:
                continue_btn = browser.page.locator(config['selectors']['continue']).first
                if continue_btn.is_visible():
                    continue_btn.click()
                    browser.wait(3000)
            except:
                pass
            
            # Enter password
            print("   Entering password...")
            password_field = browser.page.locator(config['selectors']['password']).first
            password_field.fill(creds['password'])
            browser.wait(1000)
            
            # Submit
            print("   Submitting...")
            submit_button = browser.page.locator(config['selectors']['submit']).first
            submit_button.click()

            # Wait for navigation and app to load
            print("   Waiting for Asana to load...")
            browser.wait(5000)

            # Wait for Asana's main interface to appear
            try:
                browser.page.wait_for_selector(
                    'div[class*="TopbarStructure"], div[class*="Topbar"]',
                    timeout=15000
                )
                print("✅ Asana login successful!")
                return True
            except:
                print("⚠️  Asana login may have succeeded, but couldn't confirm")
                browser.wait(5000)  # Extra wait just in case
                return True
            
        except Exception as e:
            print(f"   Asana login error: {e}")
            return False
    
    def wait_for_app_load(self, browser: BrowserAgent, app: str):
        """Wait for app-specific loading to complete"""
        print(f"⏳ Waiting for {app} to load...")
        
        # App-specific wait strategies
        if app == 'notion':
            # Wait for Notion's sidebar to appear
            try:
                browser.page.wait_for_selector('div[class*="sidebar"]', timeout=10000)
            except:
                browser.wait(5000)
        
        elif app == 'linear':
            # Wait for Linear's navigation to appear
            try:
                browser.page.wait_for_selector('nav[class*="navigation"]', timeout=10000)
            except:
                browser.wait(5000)
        
        elif app == 'asana':
            # Wait for Asana's top bar to appear
            try:
                browser.page.wait_for_selector('div[class*="TopbarStructure"]', timeout=10000)
            except:
                browser.wait(5000)
        
        else:
            # Generic wait
            browser.wait(5000)
        
        print(f"✅ {app} loaded!")