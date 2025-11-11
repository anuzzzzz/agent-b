import sys
import argparse
from pathlib import Path
from src.workflow_engine import EnhancedWorkflowEngine


def run_single_workflow(query: str, use_auth: bool = True, headless: bool = False):
    """Run a single workflow"""
    print(f"\n🚀 Running workflow: {query}")
    
    # Create engine
    engine = EnhancedWorkflowEngine(
        headless=headless,
        max_steps=15,
        use_auth=use_auth
    )
    
    # Execute workflow
    result = engine.execute_workflow(query)
    
    # Print results
    print("\n" + "="*80)
    print("📊 WORKFLOW RESULTS")
    print("="*80)
    print(f"Query: {query}")
    print(f"Status: {result['status']}")
    print(f"Steps taken: {result['step_count']}")
    print(f"Screenshots captured: {result['screenshot_count']}")
    print(f"Key states identified: {len(result.get('key_states', []))}")
    print(f"Output location: {result['task_dir']}")
    
    # Print key states
    if result.get('key_states'):
        print(f"\n🌟 Key States Captured:")
        for i, ks in enumerate(result['key_states'], 1):
            print(f"   {i}. Step {ks['step']}: {ks['screenshot'].name}")
    
    print("="*80 + "\n")
    
    return result


def run_batch_workflows(file_path: Path, use_auth: bool = True, headless: bool = False):
    """Run multiple workflows from a file"""
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"\n📋 Running {len(queries)} workflows from {file_path}")
    
    engine = EnhancedWorkflowEngine(
        headless=headless,
        max_steps=15,
        use_auth=use_auth
    )
    
    results = engine.execute_batch(queries)
    
    # Summary
    print("\n" + "="*80)
    print("📊 BATCH EXECUTION SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r['status'] == 'completed')
    failed = sum(1 for r in results if r['status'] == 'failed')
    max_steps = sum(1 for r in results if r['status'] == 'max_steps_reached')
    
    print(f"Total workflows: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Max steps reached: {max_steps}")
    
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['status'] == 'completed' else "❌"
        print(f"\n{i}. {status_icon} Status: {result['status']}")
        if 'task_dir' in result:
            print(f"   Output: {result['task_dir']}")
        if result['status'] == 'failed' and 'error' in result:
            print(f"   Error: {result['error']}")
    
    print("="*80 + "\n")
    
    return results


def run_demo_workflows():
    """Run demonstration workflows"""
    print("\n" + "="*80)
    print("🎭 RUNNING DEMONSTRATION WORKFLOWS")
    print("="*80 + "\n")
    
    demo_queries = [
        "How do I search for something on Wikipedia?",
        "How do I navigate to the main content on Example.com?",
        "How do I create a new project in Asana?",  # Requires auth
    ]
    
    print("Running 3 demonstration workflows:")
    for i, query in enumerate(demo_queries, 1):
        print(f"{i}. {query}")
    
    print("\nNote: Some workflows may require authentication.")
    print("Configure credentials in .env file if needed.\n")
    
    input("Press Enter to continue...")
    
    engine = EnhancedWorkflowEngine(
        headless=False,
        max_steps=10,
        use_auth=True
    )
    
    results = []
    for query in demo_queries:
        try:
            result = run_single_workflow(query, use_auth=True, headless=False)
            results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({'status': 'failed', 'error': str(e)})
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Run enhanced UI workflow automation'
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Natural language query for the workflow'
    )
    
    parser.add_argument(
        '--batch',
        type=Path,
        help='Path to file containing multiple queries (one per line)'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demonstration workflows'
    )
    
    parser.add_argument(
        '--no-auth',
        action='store_true',
        help='Disable authentication (for public pages only)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    parser.add_argument(
        '--max-steps',
        type=int,
        default=15,
        help='Maximum steps before stopping (default: 15)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.query and not args.batch and not args.demo:
        parser.print_help()
        print("\n❌ Error: Provide a query, --batch file, or use --demo")
        sys.exit(1)
    
    # Run appropriate mode
    if args.demo:
        run_demo_workflows()
    elif args.batch:
        run_batch_workflows(
            args.batch,
            use_auth=not args.no_auth,
            headless=args.headless
        )
    else:
        run_single_workflow(
            args.query,
            use_auth=not args.no_auth,
            headless=args.headless
        )


if __name__ == "__main__":
    main()