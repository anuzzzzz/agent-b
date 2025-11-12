#!/usr/bin/env python3
"""
Main Workflow Runner - With OAuth/Session Support

Usage:
    # First time: Setup login
    python setup_login.py
    
    # Then run workflows:
    python run_workflow.py "How do I create a project in Asana?"
"""
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.browser import PersistentBrowserAgent
from src.workflow_engine import WorkflowEngine


def run_single_workflow(query: str, use_session: bool = True, headless: bool = False):
    """Run a single workflow with session support"""
    
    print(f"\n🚀 Running workflow: {query}")
    
    # Parse the app from query (simple approach)
    app_keywords = {
        'asana': 'asana',
        'linear': 'linear', 
        'notion': 'notion',
        'github': 'github',
        'trello': 'trello',
    }
    
    session_name = 'default'
    for keyword, app in app_keywords.items():
        if keyword in query.lower():
            session_name = app
            print(f"📌 Using session: {session_name}")
            break
    
    # Create workflow engine with persistent browser
    if use_session:
        # Import the workflow engine and monkey-patch it to use persistent browser
        from src import workflow_engine as we_module
        we_module.BrowserAgent = PersistentBrowserAgent
    
    # Run the workflow
    engine = WorkflowEngine(headless=headless, max_steps=15)
    result = engine.execute_workflow(query)
    
    # Print results
    print("\n" + "="*80)
    print("📊 WORKFLOW RESULTS")
    print("="*80)
    print(f"Status: {result['status']}")
    print(f"Steps: {result['step_count']}")
    print(f"Screenshots: {result['screenshot_count']}")
    print(f"Output: {result['task_dir']}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Run UI workflow with OAuth/session support'
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Natural language query for the workflow'
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Setup login sessions'
    )
    
    parser.add_argument(
        '--no-session',
        action='store_true',
        help='Don\'t use saved sessions'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    args = parser.parse_args()
    
    if args.setup:
        # Run setup
        import setup_login
        setup_login.main()
    elif args.query:
        # Run workflow
        run_single_workflow(
            args.query,
            use_session=not args.no_session,
            headless=args.headless
        )
    else:
        parser.print_help()
        print("\n💡 First time? Run: python run_workflow.py --setup")
        print("Then: python run_workflow.py 'How do I create a project in Asana?'")


if __name__ == "__main__":
    main()