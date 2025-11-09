"""State detection for identifying when to capture screenshots"""
from playwright.sync_api import Page
from typing import Dict, Any, Optional, List
import time


class StateDetector:
    """Detects UI state changes that warrant screenshot capture"""
    
    def __init__(self, page: Page):
        self.page = page
        self.last_snapshot: Optional[Dict] = None
        
    def get_dom_snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of current DOM state
        
        Returns:
            Dictionary with DOM metrics
        """
        snapshot = self.page.evaluate("""
            () => {
                return {
                    element_count: document.querySelectorAll('*').length,
                    modal_count: document.querySelectorAll('[role="dialog"], .modal, [class*="modal"]').length,
                    form_count: document.querySelectorAll('form, [role="form"]').length,
                    button_count: document.querySelectorAll('button, [role="button"]').length,
                    url: window.location.href,
                    title: document.title,
                };
            }
        """)
        return snapshot
    
    def detect_modal(self) -> bool:
        """
        Detect if a modal/dialog is currently visible
        
        Returns:
            True if modal detected
        """
        modal_present = self.page.evaluate("""
            () => {
                // Check for common modal patterns
                const modals = document.querySelectorAll(
                    '[role="dialog"], .modal, [class*="modal"], [class*="dialog"]'
                );
                
                // Check if any are visible
                for (let modal of modals) {
                    const style = window.getComputedStyle(modal);
                    if (style.display !== 'none' && style.visibility !== 'hidden') {
                        return true;
                    }
                }
                return false;
            }
        """)
        return modal_present
    
    def detect_dropdown(self) -> bool:
        """
        Detect if a dropdown is currently open
        
        Returns:
            True if dropdown detected
        """
        dropdown_present = self.page.evaluate("""
            () => {
                // Check for common dropdown patterns
                const dropdowns = document.querySelectorAll(
                    '[role="menu"], [role="listbox"], .dropdown-menu, [class*="dropdown"][class*="open"]'
                );
                
                // Check if any are visible
                for (let dropdown of dropdowns) {
                    const style = window.getComputedStyle(dropdown);
                    if (style.display !== 'none' && style.visibility !== 'hidden') {
                        return true;
                    }
                }
                return false;
            }
        """)
        return dropdown_present
    
    def has_significant_change(self) -> bool:
        """
        Check if DOM has changed significantly since last snapshot
        
        Returns:
            True if significant change detected
        """
        current_snapshot = self.get_dom_snapshot()
        
        if not self.last_snapshot:
            self.last_snapshot = current_snapshot
            return True  # First snapshot is always significant
        
        # Check for significant changes
        changed = False
        
        # URL changed?
        if current_snapshot['url'] != self.last_snapshot['url']:
            changed = True
            print("🔍 URL changed")
        
        # New modal appeared?
        if current_snapshot['modal_count'] > self.last_snapshot['modal_count']:
            changed = True
            print("🔍 Modal appeared")
        
        # New form appeared?
        if current_snapshot['form_count'] > self.last_snapshot['form_count']:
            changed = True
            print("🔍 Form appeared")
        
        # Element count changed significantly?
        element_diff = abs(current_snapshot['element_count'] - self.last_snapshot['element_count'])
        if element_diff > 10:  # More than 10 new elements
            changed = True
            print(f"🔍 DOM changed significantly ({element_diff} elements)")
        
        # Update last snapshot
        if changed:
            self.last_snapshot = current_snapshot
        
        return changed
    
    def get_current_state_info(self) -> Dict[str, Any]:
        """
        Get information about the current UI state
        
        Returns:
            Dictionary with state information
        """
        snapshot = self.get_dom_snapshot()
        
        state_info = {
            "url": snapshot['url'],
            "title": snapshot['title'],
            "has_modal": self.detect_modal(),
            "has_dropdown": self.detect_dropdown(),
            "element_count": snapshot['element_count'],
            "modal_count": snapshot['modal_count'],
            "form_count": snapshot['form_count'],
            "timestamp": int(time.time()),
        }
        
        return state_info
    
    def wait_for_state_change(self, timeout_ms: int = 5000) -> bool:
        """
        Wait for a significant state change to occur
        
        Args:
            timeout_ms: Maximum time to wait
            
        Returns:
            True if change detected, False if timeout
        """
        start_time = time.time()
        check_interval = 200  # Check every 200ms
        
        while (time.time() - start_time) * 1000 < timeout_ms:
            if self.has_significant_change():
                return True
            time.sleep(check_interval / 1000)
        
        return False