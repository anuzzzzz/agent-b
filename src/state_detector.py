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

    def get_interactive_elements(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Extract interactive elements from the page with their selectors.

        This provides the LLM with actionable elements it can interact with,
        solving the "vision can't see CSS selectors" problem.

        Args:
            limit: Maximum number of elements to return

        Returns:
            List of interactive elements with text, role, and selector
        """
        elements = self.page.evaluate("""
            (limit) => {
                const elements = [];
                let count = 0;

                // Helper to get a good selector for an element
                function getSelector(el) {
                    // Try ID first
                    if (el.id) return `#${el.id}`;

                    // Try data attributes
                    if (el.dataset.testid) return `[data-testid="${el.dataset.testid}"]`;
                    if (el.dataset.qa) return `[data-qa="${el.dataset.qa}"]`;

                    // Try role + text
                    const role = el.getAttribute('role');
                    const text = el.textContent?.trim().substring(0, 30);
                    if (role && text) {
                        return `[role="${role}"]:has-text("${text}")`;
                    }

                    // Try aria-label
                    if (el.ariaLabel) return `[aria-label="${el.ariaLabel}"]`;

                    // Try class-based (if specific enough)
                    const classes = el.className?.split(' ').filter(c => c && !c.match(/^(css|sc|s|cls)-/));
                    if (classes && classes.length === 1) {
                        return `.${classes[0]}`;
                    }

                    // Fallback to tag + nth-child
                    const parent = el.parentElement;
                    if (parent) {
                        const siblings = Array.from(parent.children);
                        const index = siblings.indexOf(el);
                        return `${el.tagName.toLowerCase()}:nth-child(${index + 1})`;
                    }

                    return el.tagName.toLowerCase();
                }

                // Helper to check if element is visible
                function isVisible(el) {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' &&
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0';
                }

                // Collect interactive elements
                const selectors = [
                    'button',
                    '[role="button"]',
                    'a',
                    'input[type="text"]',
                    'input[type="email"]',
                    'input[type="password"]',
                    'input[type="search"]',
                    'textarea',
                    'select',
                    '[role="menuitem"]',
                    '[role="tab"]',
                    '[contenteditable]'  // Match ANY contenteditable value
                ];

                for (const selector of selectors) {
                    if (count >= limit) break;

                    const els = document.querySelectorAll(selector);
                    for (const el of els) {
                        if (count >= limit) break;
                        if (!isVisible(el)) continue;

                        const text = el.textContent?.trim() || el.value || el.placeholder || '';
                        if (!text && el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') continue;

                        elements.push({
                            selector: getSelector(el),
                            text: text.substring(0, 100),
                            role: el.getAttribute('role') || el.tagName.toLowerCase(),
                            type: el.type || 'element',
                            ariaLabel: el.ariaLabel || ''
                        });

                        count++;
                    }
                }

                return elements;
            }
        """, limit)

        return elements

    def get_focused_interactive_elements(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get interactive elements with smart prioritization based on UI state.

        When a modal/dropdown is open, prioritize elements INSIDE it.
        This solves the "too many elements" problem by focusing on relevant context.

        Args:
            limit: Maximum number of elements to return

        Returns:
            List of prioritized interactive elements
        """
        has_modal = self.detect_modal()
        has_dropdown = self.detect_dropdown()

        elements = self.page.evaluate("""
            ({limit, has_modal, has_dropdown}) => {
                const elements = [];

                // Helper functions (same as before)
                function getSelector(el) {
                    if (el.id) return `#${el.id}`;
                    if (el.dataset.testid) return `[data-testid="${el.dataset.testid}"]`;
                    if (el.dataset.qa) return `[data-qa="${el.dataset.qa}"]`;
                    const role = el.getAttribute('role');
                    const text = el.textContent?.trim().substring(0, 30);
                    if (role && text) return `[role="${role}"]:has-text("${text}")`;
                    if (el.ariaLabel) return `[aria-label="${el.ariaLabel}"]`;
                    const classes = el.className?.split(' ').filter(c => c && !c.match(/^(css|sc|s|cls)-/));
                    if (classes && classes.length === 1) return `.${classes[0]}`;
                    const parent = el.parentElement;
                    if (parent) {
                        const siblings = Array.from(parent.children);
                        const index = siblings.indexOf(el);
                        return `${el.tagName.toLowerCase()}:nth-child(${index + 1})`;
                    }
                    return el.tagName.toLowerCase();
                }

                function isVisible(el) {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' &&
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0';
                }

                // Get container to focus on
                let container = document.body;
                if (has_modal) {
                    // Focus on modal content
                    const modals = document.querySelectorAll(
                        '[role="dialog"], .modal, [class*="modal"], [class*="dialog"]'
                    );
                    for (let modal of modals) {
                        if (isVisible(modal)) {
                            container = modal;
                            break;
                        }
                    }
                } else if (has_dropdown) {
                    // Focus on dropdown content
                    const dropdowns = document.querySelectorAll(
                        '[role="menu"], [role="listbox"], .dropdown-menu, [class*="dropdown"]'
                    );
                    for (let dropdown of dropdowns) {
                        if (isVisible(dropdown)) {
                            container = dropdown;
                            break;
                        }
                    }
                }

                // Collect interactive elements from focused container
                const selectors = [
                    'input[type="text"]',
                    'input[type="email"]',
                    'input[type="password"]',
                    'input[type="search"]',
                    'textarea',
                    'select',
                    '[contenteditable]',  // Match ANY contenteditable value
                    'button',
                    '[role="button"]',
                    '[role="menuitem"]',
                    '[role="tab"]',
                    'a'
                ];

                for (const selector of selectors) {
                    if (elements.length >= limit) break;
                    const els = container.querySelectorAll(selector);
                    for (const el of els) {
                        if (elements.length >= limit) break;
                        if (!isVisible(el)) continue;

                        const text = el.textContent?.trim() || el.value || el.placeholder || '';
                        if (!text && el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA' && el.tagName !== 'SELECT') continue;

                        elements.push({
                            selector: getSelector(el),
                            text: text.substring(0, 100),
                            role: el.getAttribute('role') || el.tagName.toLowerCase(),
                            type: el.type || 'element',
                            ariaLabel: el.ariaLabel || ''
                        });
                    }
                }

                return elements;
            }
        """, {"limit": limit, "has_modal": has_modal, "has_dropdown": has_dropdown})

        return elements

    def get_elements_with_positions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get interactive elements with their visual positions (bounding boxes).

        This enables visual-first navigation where LLM describes WHAT to click,
        then we find WHERE that element is in the DOM.

        Returns elements with:
        - text: visible text
        - role: element type
        - position: {x, y, width, height} bounding box
        - selector: fallback CSS selector
        """
        elements = self.page.evaluate("""
            (limit) => {
                const elements = [];

                function isVisible(el) {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style.display !== 'none' &&
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0' &&
                           rect.width > 0 &&
                           rect.height > 0;
                }

                function getTextContent(el) {
                    // Get direct text content, not from children
                    let text = '';
                    for (let node of el.childNodes) {
                        if (node.nodeType === Node.TEXT_NODE) {
                            text += node.textContent;
                        }
                    }
                    // If no direct text, get first 100 chars from all content
                    if (!text.trim()) {
                        text = el.textContent || el.value || el.placeholder || '';
                    }
                    return text.trim().substring(0, 100);
                }

                function getSimpleSelector(el, index) {
                    // Try data attributes first
                    if (el.dataset.testid) return `[data-testid="${el.dataset.testid}"]`;
                    if (el.id) return `#${el.id}`;
                    // Fallback to nth-child with tag
                    return `${el.tagName.toLowerCase()}:nth-child(${index + 1})`;
                }

                // Collect all interactive elements
                const selectors = [
                    'button', '[role="button"]', 'a',
                    'input', 'textarea', 'select',
                    '[role="menuitem"]', '[role="tab"]',
                    '[contenteditable]'  // Match ANY contenteditable (true, plaintext-only, etc.)
                ];

                const allElements = [];
                for (const selector of selectors) {
                    const els = document.querySelectorAll(selector);
                    allElements.push(...Array.from(els));
                }

                // Filter visible, get positions, limit
                for (let i = 0; i < allElements.length && elements.length < limit; i++) {
                    const el = allElements[i];
                    if (!isVisible(el)) continue;

                    const rect = el.getBoundingClientRect();
                    const text = getTextContent(el);

                    // Skip elements with no text (unless input/textarea/contenteditable)
                    if (!text && el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA' && !el.hasAttribute('contenteditable')) continue;

                    elements.push({
                        text: text,
                        role: el.getAttribute('role') || el.tagName.toLowerCase(),
                        type: el.type || '',
                        position: {
                            x: Math.round(rect.left),
                            y: Math.round(rect.top),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            centerX: Math.round(rect.left + rect.width / 2),
                            centerY: Math.round(rect.top + rect.height / 2)
                        },
                        selector: getSimpleSelector(el, i),
                        ariaLabel: el.ariaLabel || ''
                    });
                }

                return elements;
            }
        """, limit)

        return elements