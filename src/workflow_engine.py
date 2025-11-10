"""Workflow execution engine that orchestrates the complete agent system"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import time

from .browser import BrowserAgent
from .llm_agent import LLMAgent
from .state_detector import StateDetector
from .utils import save_metadata
from .config import APP_URLS, SCREENSHOTS_DIR


class WorkflowEngine:
    """
    Main orchestrator that executes complete workflows
    
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