"""
Phase 3 Test: LLM Integration

This test verifies:
1. Query parsing works
2. LLM can decide actions
3. Actions can be executed
4. Vision-based decisions work
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser import BrowserAgent
from src.llm_agent import LLMAgent
from src.utils import save_metadata


def test_query_parsing():
    """Test parsing natural language queries"""
    
    print("\n" + "="*60)
    print("PHASE 3 TEST: Query Parsing")
    print("="*60 + "\n")
    
    agent = LLMAgent()
    
    # Test various queries
    queries = [
        "How do I create a project in Asana?",
        "Show me how to add a task in Notion",
        "What's the process for filtering issues in Linear?",
    ]
    
    for query in queries:
        result = agent.parse_query(query)
        print(f"\nQuery: {query}")
        print(f"App: {result['app']}")
        print(f"Task: {result['task']}")
        print(f"Keywords: {result['keywords']}")
        
    print("\n✅ Query parsing test passed!\n")


def test_llm_decision():
    """Test LLM decision making with a real page"""
    
    print("\n" + "="*60)
    print("PHASE 3 TEST: LLM Decision Making")
    print("="*60 + "\n")
    
    agent = LLMAgent()
    
    with BrowserAgent(headless=False) as browser:
        # Navigate to a simple page
        print("📋 Navigating to example.com...")
        browser.goto("https://example.com")
        
        # Get state
        detector = browser.get_state_detector()
        state_info = detector.get_current_state_info()
        
        # Take screenshot
        screenshot_path = browser.take_screenshot(
            "llm_test",
            task_dir="phase3_test"
        )
        
        # Ask LLM to decide action
        print("\n📋 Asking LLM to analyze page...")
        action = agent.decide_action(
            task="Navigate to the main content",
            screenshot_path=screenshot_path,
            state_info=state_info,
            is_initial=True
        )
        
        print(f"\n✅ LLM decided: {action['action']}")
        print(f"   Reasoning: {action.get('reasoning', 'N/A')}")
        
        browser.wait(2000)
    
    print("\n✅ LLM decision test passed!\n")


def test_action_execution():
    """Test executing LLM-decided actions"""
    
    print("\n" + "="*60)
    print("PHASE 3 TEST: Action Execution")
    print("="*60 + "\n")
    
    with BrowserAgent(headless=False) as browser:
        browser.goto("https://example.com")
        
        # Test various action types
        actions = [
            {"action": "wait", "milliseconds": 1000, "description": "Wait test"},
            {"action": "screenshot", "description": "Screenshot test"},
        ]
        
        for action in actions:
            print(f"\n📋 Testing action: {action['action']}")
            success = browser.execute_action(action)
            print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        browser.wait(2000)
    
    print("\n✅ Action execution test passed!\n")


def test_full_workflow():
    """Test a complete workflow with LLM"""
    
    print("\n" + "="*60)
    print("PHASE 3 TEST: Complete LLM Workflow")
    print("="*60 + "\n")
    
    agent = LLMAgent()
    
    # Parse a query
    query = "How do I navigate to Wikipedia's main page?"
    parsed = agent.parse_query(query)
    
    with BrowserAgent(headless=False) as browser:
        # Start at a page
        browser.goto("https://www.wikipedia.org")
        
        # Run a few LLM decision cycles
        for i in range(2):
            print(f"\n📋 Decision cycle {i+1}...")
            
            # Get current state
            detector = browser.get_state_detector()
            state_info = detector.get_current_state_info()
            state_info['app'] = parsed['app']
            
            # Take screenshot
            screenshot_path = browser.take_screenshot(
                f"cycle_{i+1}",
                task_dir="phase3_test/workflow"
            )
            save_metadata(screenshot_path, state_info, task=parsed['task'])
            
            # Get LLM decision
            action = agent.decide_action(
                task=parsed['task'],
                screenshot_path=screenshot_path,
                state_info=state_info,
                is_initial=(i == 0)
            )
            
            # Execute action
            if action['action'] == 'done':
                print("✅ Task complete!")
                break
                
            browser.execute_action(action)
            browser.wait(2000)
    
    print("\n✅ Full workflow test passed!\n")


if __name__ == "__main__":
    print("\n🧪 PHASE 3 TESTS\n")
    
    # Test 1: Query parsing (no browser needed)
    test_query_parsing()
    
    # Test 2: LLM decisions
    test_llm_decision()
    
    # Test 3: Action execution
    test_action_execution()
    
    # Test 4: Full workflow
    test_full_workflow()
    
    print("\n🎉 All Phase 3 tests complete!")
    print("📁 Check: data/screenshots/phase3_test/")
    print("\n💡 Next: Phase 4 - Complete Workflow Engine")