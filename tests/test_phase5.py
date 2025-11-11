"""
Phase 5 Test: Authentication & Enhanced Workflow

This test verifies:
1. Authentication handling
2. Enhanced state detection
3. Key state identification
4. Task completion detection
5. Workflow summary generation
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth_manager import AuthManager
from src.workflow_engine import EnhancedWorkflowEngine
from src.browser import BrowserAgent


def test_auth_detection():
    """Test authentication detection"""
    
    print("\n" + "="*80)
    print("PHASE 5 TEST: Authentication Detection")
    print("="*80 + "\n")
    
    auth_manager = AuthManager()
    
    with BrowserAgent(headless=False) as browser:
        # Test 1: Non-auth page
        print("📋 Test 1: Non-authenticated page (Wikipedia)")
        browser.goto("https://www.wikipedia.org")
        browser.wait(2000)
        
        requires_auth = auth_manager.requires_auth(browser, "wikipedia")
        print(f"   Requires auth: {requires_auth}")
        assert not requires_auth, "Wikipedia shouldn't require auth"
        
        # Test 2: Auth page
        print("\n📋 Test 2: Authentication page (GitHub)")
        browser.goto("https://github.com/login")
        browser.wait(2000)
        
        requires_auth = auth_manager.requires_auth(browser, "github")
        print(f"   Requires auth: {requires_auth}")
        assert requires_auth, "GitHub login page should require auth"
        
        browser.wait(2000)
    
    print("\n✅ Authentication detection test passed!\n")


def test_enhanced_state_capture():
    """Test enhanced state capture features"""
    
    print("\n" + "="*80)
    print("PHASE 5 TEST: Enhanced State Capture")
    print("="*80 + "\n")
    
    engine = EnhancedWorkflowEngine(headless=False, max_steps=2, use_auth=False)
    
    with BrowserAgent(headless=False) as browser:
        print("📋 Testing enhanced state capture...")
        browser.goto("https://example.com")
        browser.wait(2000)
        
        # Get detector
        detector = browser.get_state_detector()
        
        # Capture enhanced state
        state = engine._capture_enhanced_state(browser, detector, "example")
        
        print(f"Enhanced state captured:")
        print(f"   App: {state.get('app')}")
        print(f"   Interactive elements: {state.get('interactive_elements')}")
        print(f"   Has forms: {state.get('has_forms')}")
        print(f"   Success indicators: {state.get('has_success_indicator')}")
        print(f"   Visible text: {state.get('visible_text_summary', '')[:50]}...")
        
        assert state['app'] == 'example'
        assert 'interactive_elements' in state
        
        browser.wait(2000)
    
    print("\n✅ Enhanced state capture test passed!\n")


def test_key_state_detection():
    """Test key state identification"""
    
    print("\n" + "="*80)
    print("PHASE 5 TEST: Key State Detection")
    print("="*80 + "\n")
    
    engine = EnhancedWorkflowEngine(headless=False, max_steps=2, use_auth=False)
    
    # Test different state scenarios
    test_states = [
        {
            'has_modal': True,
            'has_forms': False,
            'visible_text_summary': 'Create Project',
            'expected': True,
            'description': 'Modal state'
        },
        {
            'has_modal': False,
            'has_forms': True,
            'visible_text_summary': 'Enter details',
            'expected': True,
            'description': 'Form state'
        },
        {
            'has_modal': False,
            'has_forms': False,
            'has_success_indicator': True,
            'visible_text_summary': 'Successfully created',
            'expected': True,
            'description': 'Success state'
        },
        {
            'has_modal': False,
            'has_forms': False,
            'visible_text_summary': 'Welcome page',
            'expected': False,
            'description': 'Normal page'
        }
    ]
    
    for state in test_states:
        is_key = engine._is_key_state(state, "Create a project")
        print(f"📋 {state['description']}: {'✅ Key' if is_key else '❌ Not key'}")
        assert is_key == state['expected'], f"Failed for {state['description']}"
    
    print("\n✅ Key state detection test passed!\n")


def test_workflow_summary():
    """Test workflow summary generation"""
    
    print("\n" + "="*80)
    print("PHASE 5 TEST: Workflow Summary")
    print("="*80 + "\n")
    
    engine = EnhancedWorkflowEngine(headless=False, max_steps=2, use_auth=False)
    
    # Create mock workflow result
    mock_result = {
        'status': 'completed',
        'step_count': 5,
        'screenshot_count': 6,
        'key_states': [
            {
                'step': 2,
                'screenshot': Path('02_form.png'),
                'state': {'has_forms': True}
            },
            {
                'step': 4,
                'screenshot': Path('04_success.png'),
                'state': {'has_success_indicator': True}
            }
        ],
        'actions': [
            {'action': 'click', 'description': 'Create button'},
            {'action': 'fill', 'description': 'Project name'},
            {'action': 'click', 'description': 'Submit'},
            {'action': 'screenshot', 'description': 'Success state'},
            {'action': 'done', 'description': 'Task complete'}
        ]
    }
    
    summary = engine.generate_workflow_summary(mock_result)
    
    print("Generated summary:")
    print(f"   Status: {summary['status']}")
    print(f"   Steps: {summary['total_steps']}")
    print(f"   Key states: {summary['key_states_captured']}")
    print(f"   Actions: {len(summary['actions_summary'])}")
    
    assert summary['status'] == 'completed'
    assert summary['key_states_captured'] == 2
    assert len(summary['actions_summary']) == 5
    
    print("\n✅ Workflow summary test passed!\n")


def test_simple_enhanced_workflow():
    """Test a simple workflow with enhanced features"""
    
    print("\n" + "="*80)
    print("PHASE 5 TEST: Simple Enhanced Workflow")
    print("="*80 + "\n")
    
    engine = EnhancedWorkflowEngine(
        headless=False,
        max_steps=3,
        use_auth=False  # Skip auth for simple test
    )
    
    query = "How do I navigate to Wikipedia?"
    
    result = engine.execute_workflow(query)
    
    print(f"\n✅ Enhanced workflow completed!")
    print(f"   Status: {result['status']}")
    print(f"   Steps: {result['step_count']}")
    print(f"   Key states: {len(result.get('key_states', []))}")
    
    # Check that summary was created
    task_dir = result['task_dir']
    summary_file = task_dir / 'workflow_summary.json'
    assert summary_file.exists(), "Summary file should exist"
    
    # Load and check summary
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    print(f"\n📊 Workflow Summary:")
    print(f"   Status: {summary['status']}")
    print(f"   Total steps: {summary['total_steps']}")
    print(f"   Key states captured: {summary['key_states_captured']}")
    
    print("\n✅ Simple enhanced workflow test passed!\n")


def test_auth_credentials():
    """Test credentials loading"""
    
    print("\n" + "="*80)
    print("PHASE 5 TEST: Credentials Management")
    print("="*80 + "\n")
    
    auth_manager = AuthManager()
    
    print("Checking for available credentials:")
    for app in ['linear', 'notion', 'asana', 'github']:
        has_creds = auth_manager.has_credentials(app)
        print(f"   {app}: {'✅ Available' if has_creds else '❌ Not configured'}")
    
    print("\nNote: Configure credentials in .env file or credentials.json")
    print("See .env.credentials.example for format")
    
    print("\n✅ Credentials check complete!\n")


if __name__ == "__main__":
    print("\n🧪 PHASE 5 TESTS: Authentication & Enhanced Workflow\n")
    
    # Test 1: Auth detection
    test_auth_detection()
    
    # Test 2: Enhanced state capture
    test_enhanced_state_capture()
    
    # Test 3: Key state detection
    test_key_state_detection()
    
    # Test 4: Workflow summary
    test_workflow_summary()
    
    # Test 5: Simple enhanced workflow
    test_simple_enhanced_workflow()
    
    # Test 6: Credentials check
    test_auth_credentials()
    
    print("\n🎉 All Phase 5 tests complete!")
    print("📁 Check: data/screenshots/")
    print("\n💡 Next: Phase 6 - Production Workflows with Real Apps")