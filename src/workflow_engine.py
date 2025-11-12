"""Workflow execution engine - both basic and enhanced versions"""
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import time
import json

from .browser import PersistentBrowserAgent as BrowserAgent
from .llm_agent import LLMAgent
from .state_detector import StateDetector
from .som_annotator import SoMAnnotator
from .utils import save_metadata
from .config import SCREENSHOTS_DIR, APP_URLS

try:
    from .auth_manager import AuthManager
except ImportError:
    AuthManager = None


class EnhancedWorkflowEngine:
    """
    Enhanced orchestrator with authentication and better state management
    """
    
    def __init__(
        self,
        headless: bool = False,
        max_steps: int = 20,
        use_auth: bool = True,
        use_session: bool = False,
        credentials_path: Optional[Path] = None
    ):
        """
        Initialize enhanced workflow engine

        Args:
            headless: Run browser in headless mode
            max_steps: Maximum actions before stopping
            use_auth: Whether to attempt authentication
            use_session: Whether to use saved browser sessions (for OAuth)
            credentials_path: Optional path to credentials JSON
        """
        self.headless = headless
        self.max_steps = max_steps
        self.use_auth = use_auth
        self.use_session = use_session
        self.llm_agent = LLMAgent()
        self.auth_manager = AuthManager(credentials_path) if use_auth else None
        self.key_states = []  # Track important states
        
    def execute_workflow(self, query: str) -> Dict[str, Any]:
        """
        Execute a complete workflow with authentication
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with workflow results
        """
        print("\n" + "="*80)
        print(f"🚀 EXECUTING ENHANCED WORKFLOW")
        print(f"📝 Query: {query}")
        print("="*80 + "\n")
        
        # Parse the query
        parsed = self.llm_agent.parse_query(query)
        app = parsed['app']
        task = parsed['task']
        
        print(f"📋 Task: {task}")
        print(f"🎯 App: {app}")
        
        # Get app URL
        app_url = self._get_app_url(app)
        
        # Create task directory
        task_dir = self._create_task_directory(app, task)
        print(f"📁 Saving to: {task_dir}")
        
        # Save workflow metadata
        self._save_workflow_metadata(task_dir, query, parsed)
        
        # Execute workflow
        workflow_result = self._run_enhanced_workflow_loop(
            task=task,
            app=app,
            app_url=app_url,
            task_dir=task_dir
        )
        
        # Generate summary
        summary = self.generate_workflow_summary(workflow_result)
        
        # Save summary
        self._save_workflow_summary(task_dir, summary)
        
        print("\n" + "="*80)
        print(f"✅ ENHANCED WORKFLOW COMPLETE")
        print(f"   Status: {workflow_result['status']}")
        print(f"   Steps: {workflow_result['step_count']}")
        print(f"   Screenshots: {workflow_result['screenshot_count']}")
        print(f"   Key States: {len(workflow_result.get('key_states', []))}")
        print("="*80 + "\n")
        
        return workflow_result
    
    def _run_enhanced_workflow_loop(
        self,
        task: str,
        app: str,
        app_url: str,
        task_dir: Path
    ) -> Dict[str, Any]:
        """
        Enhanced workflow execution with auth and better state tracking
        """
        screenshots = []
        actions_taken = []
        key_states = []
        step_count = 0
        consecutive_failures = 0
        max_failures = 3

        # Choose browser type based on session preference
        # BrowserAgent is actually PersistentBrowserAgent - it always uses sessions
        if self.use_session:
            print(f"🔄 Using persistent session for {app}")
            browser = BrowserAgent(
                headless=self.headless,
                session_name=app
            )
        else:
            # Use default session for non-session workflows
            browser = BrowserAgent(
                headless=self.headless,
                session_name="default"
            )

        with browser:
            # Step 0: Navigate to app
            print(f"\n📍 Step 0: Navigating to {app_url}")
            browser.goto(app_url)
            browser.wait(3000)

            # Handle authentication - GENERALIZED (no app-specific logic)
            if self.use_session:
                # Using persistent session - trust that login was done via setup_login.py
                print("✅ Using persistent session - assuming authenticated")
                print(f"   (If login fails, run: python setup_login.py {app})")
            elif self.use_auth:
                # Not using session - remind user about session setup
                print("\n⚠️  Running without --use-session flag")
                print("   For OAuth/SSO apps, use --use-session after running setup_login.py")
                print("   Continuing with current page state...")
            
            # Get state detector
            detector = browser.get_state_detector()
            
            # Main workflow loop
            while step_count < self.max_steps:
                step_count += 1
                
                print(f"\n{'─'*80}")
                print(f"🔄 Step {step_count}/{self.max_steps}")
                print(f"{'─'*80}")
                
                # 1. OBSERVE: Capture current state
                state_info = self._capture_enhanced_state(browser, detector, app)
                state_info['step'] = step_count
                
                print(f"👁️  State Analysis:")
                print(f"   URL: {state_info['url'][:60]}...")
                print(f"   Title: {state_info['title'][:60]}...")
                print(f"   Elements: {state_info['element_count']}")
                print(f"   Interactive: {state_info.get('interactive_elements', 'N/A')}")
                
                # 2. CAPTURE: Take screenshot
                screenshot_name = f"{step_count:02d}_{self._generate_state_name(state_info)}"
                screenshot_path = browser.take_screenshot(
                    screenshot_name,
                    task_dir=task_dir
                )
                screenshots.append(screenshot_path)
                
                # Save metadata
                save_metadata(screenshot_path, state_info, task=task)
                
                # 3. CHECK FOR KEY STATE
                if self._is_key_state(state_info, task):
                    print("🌟 Key state detected!")
                    key_states.append({
                        'step': step_count,
                        'screenshot': screenshot_path,
                        'state': state_info
                    })
                
                # 4. SET-OF-MARKS (SoM): Extract elements and annotate screenshot
                print(f"   🎯 Applying Set-of-Marks annotation...")

                # Get interactive elements with positions
                elements = detector.get_elements_with_positions(limit=100)
                print(f"   Found {len(elements)} interactive elements")

                # Annotate screenshot with numbered marks
                annotator = SoMAnnotator()
                annotated_screenshot, element_mapping = annotator.annotate_screenshot(
                    screenshot_path,
                    elements
                )
                print(f"   ✓ Screenshot annotated with {len(element_mapping)} marks")

                # 5. DECIDE: Ask LLM what to do next (with annotated screenshot)
                print(f"🤔 Deciding next action...")
                action = self.llm_agent.decide_action(
                    task=task,
                    screenshot_path=annotated_screenshot,  # Use annotated screenshot!
                    state_info=state_info,
                    is_initial=(step_count == 1),
                    interactive_elements=None,  # Not needed, LLM uses element IDs
                    element_mapping=element_mapping  # Pass mapping for context
                )
                
                print(f"💡 Decision: {action['action']}")
                if 'reasoning' in action:
                    print(f"   Reasoning: {action['reasoning'][:100]}...")
                
                actions_taken.append(action)
                
                # 5. CHECK COMPLETION
                if action['action'] == 'done' or self._detect_task_completion(task, state_info, actions_taken):
                    print("✅ Task completed successfully!")
                    return {
                        'status': 'completed',
                        'step_count': step_count,
                        'screenshot_count': len(screenshots),
                        'screenshots': screenshots,
                        'actions': actions_taken,
                        'key_states': key_states,
                        'task_dir': task_dir,
                    }
                
                # 6. ACT: Execute the action
                print(f"⚡ Executing: {action.get('description', action['action'])}")
                success = browser.execute_action(action, element_mapping=element_mapping)
                
                if not success:
                    consecutive_failures += 1
                    print(f"⚠️  Action failed ({consecutive_failures}/{max_failures})")
                    
                    if consecutive_failures >= max_failures:
                        print("❌ Too many consecutive failures")
                        return {
                            'status': 'failed',
                            'step_count': step_count,
                            'screenshot_count': len(screenshots),
                            'screenshots': screenshots,
                            'actions': actions_taken,
                            'key_states': key_states,
                            'task_dir': task_dir,
                            'error': 'Too many action failures'
                        }
                else:
                    consecutive_failures = 0  # Reset on success
                
                # Wait for state to settle
                browser.wait(2000)
                
                # Check for significant state change
                if detector.has_significant_change():
                    print("🔍 Significant state change detected")
                    
                    # Capture transition state if modal/dropdown appeared
                    if detector.detect_modal() or detector.detect_dropdown():
                        print("📸 Capturing transition state...")
                        transition_screenshot = browser.take_screenshot(
                            f"{step_count:02d}b_transition",
                            task_dir=task_dir
                        )
                        screenshots.append(transition_screenshot)
            
            # Hit max steps
            print(f"\n⚠️  Reached maximum steps ({self.max_steps})")
            return {
                'status': 'max_steps_reached',
                'step_count': step_count,
                'screenshot_count': len(screenshots),
                'screenshots': screenshots,
                'actions': actions_taken,
                'key_states': key_states,
                'task_dir': task_dir,
            }
    
    def _capture_enhanced_state(
        self,
        browser: BrowserAgent,
        detector: StateDetector,
        app: str
    ) -> Dict[str, Any]:
        """Capture enhanced state information"""
        base_state = detector.get_current_state_info()
        
        # Add enhanced information
        enhanced_state = {
            **base_state,
            'app': app,
            'interactive_elements': self._count_interactive_elements(browser),
            'has_forms': self._detect_forms(browser),
            'has_success_indicator': self._detect_success_indicators(browser),
            'visible_text_summary': self._get_visible_text_summary(browser),
        }
        
        return enhanced_state
    
    def _count_interactive_elements(self, browser: BrowserAgent) -> int:
        """Count interactive elements on the page"""
        try:
            return browser.page.evaluate("""
                () => {
                    const interactive = document.querySelectorAll(
                        'button, a, input, textarea, select, [role="button"], [onclick]'
                    );
                    return interactive.length;
                }
            """)
        except:
            return 0
    
    def _detect_forms(self, browser: BrowserAgent) -> bool:
        """Detect if there are forms on the page"""
        try:
            return browser.page.evaluate("""
                () => {
                    const forms = document.querySelectorAll('form, [role="form"]');
                    const inputs = document.querySelectorAll('input, textarea, select');
                    return forms.length > 0 || inputs.length > 2;
                }
            """)
        except:
            return False
    
    def _detect_success_indicators(self, browser: BrowserAgent) -> bool:
        """Detect success indicators (toasts, alerts, success messages)"""
        try:
            return browser.page.evaluate("""
                () => {
                    // Look for success indicators
                    const selectors = [
                        '[class*="success"]', '[class*="toast"]', '[class*="alert"]',
                        '[role="alert"]', '[class*="notification"]',
                        ':contains("successfully")', ':contains("created")',
                        ':contains("saved")', ':contains("completed")'
                    ];
                    
                    for (let selector of selectors) {
                        try {
                            if (document.querySelector(selector)) return true;
                        } catch (e) {}
                    }
                    
                    // Check for success in text
                    const bodyText = document.body.innerText.toLowerCase();
                    const successWords = ['success', 'created', 'saved', 'completed', 'done'];
                    return successWords.some(word => bodyText.includes(word));
                }
            """)
        except:
            return False
    
    def _get_visible_text_summary(self, browser: BrowserAgent) -> str:
        """Get a summary of visible text on the page"""
        try:
            text = browser.page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('h1, h2, h3, button, [role="button"]');
                    const texts = Array.from(elements)
                        .map(el => el.innerText?.trim())
                        .filter(text => text && text.length > 0)
                        .slice(0, 10);
                    return texts.join(' | ');
                }
            """)
            return text[:200] if text else ""
        except:
            return ""
    
    def _is_key_state(self, state_info: Dict[str, Any], task: str) -> bool:
        """Determine if current state is a key state for the task"""
        # Key states are typically:
        # - Forms (create/edit states)
        # - Modals
        # - Success states
        # - List/grid views (for navigation tasks)
        
        if state_info.get('has_modal'):
            return True
        
        if state_info.get('has_forms'):
            return True
        
        if state_info.get('has_success_indicator'):
            return True
        
        # Task-specific key states
        task_lower = task.lower()
        if 'create' in task_lower and 'form' in state_info.get('visible_text_summary', '').lower():
            return True
        
        if 'filter' in task_lower and 'filter' in state_info.get('visible_text_summary', '').lower():
            return True
        
        return False
    
    def _detect_task_completion(
        self,
        task: str,  # Keep for interface compatibility
        current_state: Dict[str, Any],  # Keep for interface compatibility
        actions_taken: List[Dict]
    ) -> bool:
        """
        Detect if the task has been completed.

        GENERALIZATION: We do NOT hardcode task-specific completion logic.
        The LLM is fully responsible for deciding when to return "done".
        This method now always returns False - completion is LLM-driven only.

        This maintains the interface but removes all hardcoded heuristics.
        """
        # Always return False - let the LLM decide completion via "done" action
        return False
    
    def _generate_state_name(self, state_info: Dict[str, Any]) -> str:
        """Generate descriptive name for current state"""
        if state_info.get('has_modal'):
            return "modal"
        elif state_info.get('has_forms'):
            return "form"
        elif state_info.get('has_dropdown'):
            return "dropdown"
        elif state_info.get('has_success_indicator'):
            return "success"
        else:
            # Use page title or URL path
            title = state_info.get('title', '').lower()
            if title:
                return title.replace(' ', '_')[:20]
            return "state"
    
    def _get_app_url(self, app: str) -> str:
        """
        Get URL for app using smart heuristics for authenticated apps.

        GENERALIZATION: Uses config for known apps, falls back to common patterns.
        Prioritizes authenticated/app subdomains since we use persistent sessions.

        Common patterns:
        - app.{name}.com (Asana, etc.)
        - {name}.app (Linear, etc.)
        - www.{name}.so (Notion)
        - www.{name}.com (generic fallback)
        """
        app_lower = app.lower()

        # Special case: "other" means example.com for testing
        if app_lower == "other":
            return "https://example.com"

        # Use configured URL if available
        if app_lower in APP_URLS:
            return APP_URLS[app_lower]

        # Fallback to authenticated app subdomain (most common for SaaS apps)
        # This works better with persistent sessions
        return f"https://app.{app_lower}.com"
    
    def _create_task_directory(self, app: str, task: str) -> Path:
        """Create organized directory structure"""
        # Clean names for directory
        app_clean = ''.join(c for c in app.lower() if c.isalnum() or c == '_')
        task_clean = ''.join(c for c in task.lower().replace(' ', '_') if c.isalnum() or c == '_')
        task_clean = task_clean[:50]
        
        # Create timestamped directory
        timestamp = int(time.time())
        task_dir = SCREENSHOTS_DIR / app_clean / f"{task_clean}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)
        
        return task_dir
    
    def _save_workflow_metadata(self, task_dir: Path, query: str, parsed: Dict):
        """Save workflow metadata"""
        metadata = {
            'query': query,
            'parsed': parsed,
            'timestamp': int(time.time()),
            'engine_version': '2.0',
            'features': {
                'authentication': self.use_auth,
                'max_steps': self.max_steps,
            }
        }
        
        metadata_path = task_dir / 'workflow_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _save_workflow_summary(self, task_dir: Path, summary: Dict):
        """Save workflow summary"""
        summary_path = task_dir / 'workflow_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def generate_workflow_summary(self, result: Dict) -> Dict:
        """Generate human-readable workflow summary"""
        summary = {
            'status': result['status'],
            'total_steps': result['step_count'],
            'total_screenshots': result['screenshot_count'],
            'key_states_captured': len(result.get('key_states', [])),
            'actions_summary': self._summarize_actions(result.get('actions', [])),
            'key_states': [
                {
                    'step': ks['step'],
                    'type': self._generate_state_name(ks['state']),
                    'screenshot': str(ks['screenshot'].name)
                }
                for ks in result.get('key_states', [])
            ],
            'completion_reason': result.get('status', 'unknown'),
        }
        
        if result['status'] == 'failed':
            summary['error'] = result.get('error', 'Unknown error')
        
        return summary
    
    def _summarize_actions(self, actions: List[Dict]) -> List[str]:
        """Create concise summary of actions taken"""
        summary = []
        for action in actions:
            action_type = action.get('action', 'unknown')
            description = action.get('description', '')
            
            if action_type == 'click':
                summary.append(f"Clicked: {description or action.get('selector', 'element')}")
            elif action_type == 'fill':
                summary.append(f"Filled: {description or 'form field'}")
            elif action_type == 'wait':
                summary.append(f"Waited: {action.get('milliseconds', 0)}ms")
            elif action_type == 'screenshot':
                summary.append(f"Captured: {description or 'state'}")
            elif action_type == 'done':
                summary.append("Completed task")
        
        return summary
    
    def execute_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple workflows in batch"""
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*80}")
            print(f"BATCH EXECUTION: {i}/{len(queries)}")
            print(f"{'='*80}")
            
            try:
                result = self.execute_workflow(query)
                results.append(result)
            except Exception as e:
                print(f"❌ Workflow failed: {e}")
                results.append({
                    'status': 'failed',
                    'error': str(e),
                    'query': query,
                })
            
            # Pause between workflows
            if i < len(queries):
                print(f"\n⏸️  Pausing 5 seconds before next workflow...")
                time.sleep(5)

        return results


class WorkflowEngine:
    """
    Basic workflow orchestrator (for Phase 4 tests)

    This class ties together all components:
    - Browser automation (Phase 1)
    - State detection (Phase 2)
    - LLM decision making (Phase 3)
    """

    def __init__(self, headless: bool = False, max_steps: int = 20):
        """
        Initialize workflow engine

        Args:
            headless: Run browser in headless mode
            max_steps: Maximum actions before stopping (safety)
        """
        self.headless = headless
        self.max_steps = max_steps
        self.llm_agent = LLMAgent()

    def execute_workflow(self, query: str) -> Dict[str, Any]:
        """
        Execute a complete workflow from natural language query

        Args:
            query: Natural language query (e.g., "How do I create a project in Asana?")

        Returns:
            Dictionary with workflow results
        """
        print("\n" + "="*80)
        print(f"🚀 EXECUTING WORKFLOW: {query}")
        print("="*80 + "\n")

        # Parse the query
        parsed = self.llm_agent.parse_query(query)
        app = parsed['app']
        task = parsed['task']

        print(f"📋 Task: {task}")
        print(f"🎯 App: {app}")

        # Get app URL
        app_url = APP_URLS.get(app.lower())
        if not app_url:
            print(f"⚠️  Unknown app: {app}, using generic approach")
            # Try common URL patterns
            if app.lower() == "other":
                app_url = "https://example.com"  # Safe fallback
            else:
                app_url = f"https://www.{app.lower()}.com"

        # Create task directory for screenshots
        task_dir = self._create_task_directory(app, task)
        print(f"📁 Saving to: {task_dir}")

        # Execute workflow
        workflow_result = self._run_workflow_loop(
            task=task,
            app=app,
            app_url=app_url,
            task_dir=task_dir
        )

        print("\n" + "="*80)
        print(f"✅ WORKFLOW COMPLETE")
        print(f"   Steps taken: {workflow_result['step_count']}")
        print(f"   Screenshots: {workflow_result['screenshot_count']}")
        print(f"   Status: {workflow_result['status']}")
        print("="*80 + "\n")

        return workflow_result

    def _run_workflow_loop(
        self,
        task: str,
        app: str,
        app_url: str,
        task_dir: Path
    ) -> Dict[str, Any]:
        """
        Main workflow execution loop

        Args:
            task: Task description
            app: App name
            app_url: Starting URL
            task_dir: Directory to save screenshots

        Returns:
            Workflow result dictionary
        """
        screenshots = []
        actions_taken = []
        step_count = 0

        with BrowserAgent(headless=self.headless) as browser:
            # Step 0: Navigate to app
            print(f"\n📍 Step 0: Navigating to {app_url}")
            browser.goto(app_url)
            browser.wait(2000)  # Wait for initial load

            # Get state detector
            detector = browser.get_state_detector()

            # Main loop
            while step_count < self.max_steps:
                step_count += 1

                print(f"\n{'─'*80}")
                print(f"🔄 Step {step_count}/{self.max_steps}")
                print(f"{'─'*80}")

                # 1. OBSERVE: Capture current state
                state_info = detector.get_current_state_info()
                state_info['app'] = app
                state_info['step'] = step_count

                print(f"👁️  Observing state:")
                print(f"   - URL: {state_info['url'][:50]}...")
                print(f"   - Title: {state_info['title'][:50]}...")
                print(f"   - Modal: {state_info['has_modal']}")
                print(f"   - Dropdown: {state_info['has_dropdown']}")

                # 2. CAPTURE: Take screenshot
                screenshot_name = f"{step_count:02d}_state"
                screenshot_path = browser.take_screenshot(
                    screenshot_name,
                    task_dir=task_dir
                )
                screenshots.append(screenshot_path)

                # Save metadata
                save_metadata(screenshot_path, state_info, task=task)

                # 3. DECIDE: Ask LLM what to do next
                print(f"🤔 Asking LLM for decision...")
                action = self.llm_agent.decide_action(
                    task=task,
                    screenshot_path=screenshot_path,
                    state_info=state_info,
                    is_initial=(step_count == 1)
                )

                print(f"💡 Decision: {action['action']}")
                print(f"   Reasoning: {action.get('reasoning', 'N/A')[:100]}...")

                actions_taken.append(action)

                # 4. CHECK: Are we done?
                if action['action'] == 'done':
                    print(f"✅ Task completed!")
                    return {
                        'status': 'completed',
                        'step_count': step_count,
                        'screenshot_count': len(screenshots),
                        'screenshots': screenshots,
                        'actions': actions_taken,
                        'task_dir': task_dir,
                    }

                # 5. ACT: Execute the action
                print(f"⚡ Executing action...")
                success = browser.execute_action(action)

                if not success:
                    print(f"⚠️  Action failed, but continuing...")

                # Wait for state to settle
                browser.wait(2000)

                # Check if state changed significantly
                if detector.has_significant_change():
                    print(f"🔍 Significant state change detected!")

            # Hit max steps
            print(f"\n⚠️  Reached maximum steps ({self.max_steps})")
            return {
                'status': 'max_steps_reached',
                'step_count': step_count,
                'screenshot_count': len(screenshots),
                'screenshots': screenshots,
                'actions': actions_taken,
                'task_dir': task_dir,
            }

    def _create_task_directory(self, app: str, task: str) -> Path:
        """
        Create organized directory for task screenshots

        Args:
            app: App name
            task: Task description

        Returns:
            Path to task directory
        """
        # Clean task name for directory
        task_name = task.lower()
        task_name = task_name.replace(" ", "_")
        task_name = ''.join(c for c in task_name if c.isalnum() or c == '_')
        task_name = task_name[:50]  # Limit length

        # Create directory: data/screenshots/{app}/{task_name}_{timestamp}/
        timestamp = int(time.time())
        task_dir = SCREENSHOTS_DIR / app.lower() / f"{task_name}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)

        return task_dir

    def execute_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple workflows in batch

        Args:
            queries: List of natural language queries

        Returns:
            List of workflow results
        """
        results = []

        for i, query in enumerate(queries, 1):
            print(f"\n{'='*80}")
            print(f"BATCH EXECUTION: {i}/{len(queries)}")
            print(f"{'='*80}")

            try:
                result = self.execute_workflow(query)
                results.append(result)
            except Exception as e:
                print(f"❌ Workflow failed: {e}")
                results.append({
                    'status': 'failed',
                    'error': str(e),
                    'query': query,
                })

            # Brief pause between workflows
            if i < len(queries):
                print(f"\n⏸️  Pausing 5 seconds before next workflow...")
                time.sleep(5)

        return results