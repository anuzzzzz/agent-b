"""
Phase 4 Test: Workflow Engine

This test verifies:
1. Complete workflow execution
2. Observe → Decide → Act loop
3. Screenshot organization
4. Stopping conditions
5. Batch execution
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflow_engine import WorkflowEngine


def test_simple_workflow():
    """Test a simple workflow execution"""
    
    print("\n" + "="*80)
    print("PHASE 4 TEST: Simple Workflow")
    print("="*80 + "\n")
    
    engine = WorkflowEngine(headless=False, max_steps=5)
    
    # Simple query
    query = "How do I navigate to the main page of Wikipedia?"
    
    result = engine.execute_workflow(query)
    
    print(f"\n✅ Workflow completed!")
    print(f"   Status: {result['status']}")
    print(f"   Steps: {result['step_count']}")
    print(f"   Screenshots: {result['screenshot_count']}")
    print(f"   Directory: {result['task_dir']}")
    
    # Verify screenshots exist
    assert result['screenshot_count'] > 0, "Should have screenshots"
    for screenshot in result['screenshots']:
        assert screenshot.exists(), f"Screenshot should exist: {screenshot}"
    
    print("\n✅ Simple workflow test passed!\n")


def test_app_workflow():
    """Test workflow with a real app"""
    
    print("\n" + "="*80)
    print("PHASE 4 TEST: App Workflow (Asana)")
    print("="*80 + "\n")
    
    engine = WorkflowEngine(headless=False, max_steps=3)
    
    # Note: This won't actually create a project (no login)
    # But it will navigate and explore the interface
    query = "How do I create a project in Asana?"
    
    result = engine.execute_workflow(query)
    
    print(f"\n✅ App workflow completed!")
    print(f"   Status: {result['status']}")
    print(f"   Steps: {result['step_count']}")
    
    # Check directory structure
    task_dir = result['task_dir']
    print(f"   Task directory: {task_dir}")
    
    # List screenshots
    screenshots = list(task_dir.glob("*.png"))
    metadata_files = list(task_dir.glob("*.json"))
    
    print(f"   Screenshots: {len(screenshots)}")
    print(f"   Metadata files: {len(metadata_files)}")
    
    assert len(screenshots) > 0, "Should have screenshots"
    assert len(metadata_files) > 0, "Should have metadata"
    
    print("\n✅ App workflow test passed!\n")


def test_batch_execution():
    """Test executing multiple workflows"""
    
    print("\n" + "="*80)
    print("PHASE 4 TEST: Batch Execution")
    print("="*80 + "\n")
    
    engine = WorkflowEngine(headless=False, max_steps=3)
    
    queries = [
        "How do I search on Wikipedia?",
        "How do I navigate to the about page on Example.com?",
    ]
    
    results = engine.execute_batch(queries)
    
    print(f"\n✅ Batch execution completed!")
    print(f"   Total workflows: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"   Workflow {i}: {result['status']} ({result.get('step_count', 0)} steps)")
    
    assert len(results) == len(queries), "Should have results for all queries"
    
    print("\n✅ Batch execution test passed!\n")


def test_max_steps_limit():
    """Test that max_steps prevents infinite loops"""
    
    print("\n" + "="*80)
    print("PHASE 4 TEST: Max Steps Limit")
    print("="*80 + "\n")
    
    engine = WorkflowEngine(headless=False, max_steps=2)  # Very low limit
    
    query = "How do I use Wikipedia?"
    
    result = engine.execute_workflow(query)
    
    print(f"\n✅ Max steps test completed!")
    print(f"   Status: {result['status']}")
    print(f"   Steps taken: {result['step_count']}")
    
    # Should hit the limit
    assert result['step_count'] == 2, "Should stop at max_steps"
    assert result['status'] == 'max_steps_reached', "Should indicate max steps"
    
    print("\n✅ Max steps test passed!\n")


def test_directory_structure():
    """Test that directory structure is organized correctly"""
    
    print("\n" + "="*80)
    print("PHASE 4 TEST: Directory Structure")
    print("="*80 + "\n")
    
    engine = WorkflowEngine(headless=False, max_steps=2)
    
    query = "How do I create a project in Asana?"
    
    result = engine.execute_workflow(query)
    
    task_dir = result['task_dir']
    
    print(f"Task directory: {task_dir}")
    
    # Check structure: data/screenshots/{app}/{task}/
    assert 'asana' in str(task_dir).lower(), "Should be in app directory"
    assert 'create' in str(task_dir) or 'project' in str(task_dir), "Should contain task name"
    
    # Check files
    png_files = list(task_dir.glob("*.png"))
    json_files = list(task_dir.glob("*.json"))
    
    print(f"   PNG files: {len(png_files)}")
    print(f"   JSON files: {len(json_files)}")
    
    assert len(png_files) > 0, "Should have screenshots"
    assert len(json_files) > 0, "Should have metadata"
    assert len(png_files) == len(json_files), "Each screenshot should have metadata"
    
    print("\n✅ Directory structure test passed!\n")


if __name__ == "__main__":
    print("\n🧪 PHASE 4 TESTS\n")
    
    # Test 1: Simple workflow
    test_simple_workflow()
    
    # Test 2: App workflow
    test_app_workflow()
    
    # Test 3: Max steps
    test_max_steps_limit()
    
    # Test 4: Directory structure
    test_directory_structure()
    
    # Test 5: Batch execution
    test_batch_execution()
    
    print("\n🎉 All Phase 4 tests complete!")
    print("📁 Check: data/screenshots/")
    print("\n💡 Next: Phase 5 - Real Asana Workflows")