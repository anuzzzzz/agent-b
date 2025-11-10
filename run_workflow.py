"""
Simple script to run a workflow

Usage:
    python run_workflow.py "How do I create a project in Asana?"
"""
import sys
from src.workflow_engine import WorkflowEngine


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_workflow.py \"Your query here\"")
        print("\nExamples:")
        print('  python run_workflow.py "How do I search on Wikipedia?"')
        print('  python run_workflow.py "How do I create a project in Asana?"')
        sys.exit(1)
    
    query = sys.argv[1]
    
    # Create engine (visible browser, max 10 steps)
    engine = WorkflowEngine(headless=False, max_steps=10)
    
    # Execute workflow
    result = engine.execute_workflow(query)
    
    # Print summary
    print("\n" + "="*80)
    print("WORKFLOW SUMMARY")
    print("="*80)
    print(f"Query: {query}")
    print(f"Status: {result['status']}")
    print(f"Steps: {result['step_count']}")
    print(f"Screenshots: {result['screenshot_count']}")
    print(f"Location: {result['task_dir']}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()