#!/usr/bin/env python3
"""
Setup Login Sessions - Manual OAuth/SSO Login Handler

This script opens a browser window where you can manually log in to apps
that use OAuth/SSO (like Asana with Google). The session will be saved
and reused in subsequent workflow runs.

Usage:
    python setup_login.py asana
    python setup_login.py linear
    python setup_login.py notion
    python setup_login.py --list
"""
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.browser import PersistentBrowserAgent
from src.config import APP_URLS


def setup_login_for_app(app: str):
    """
    Open browser for manual login and save session

    Args:
        app: App name (e.g., 'asana', 'linear', 'notion')
    """
    app = app.lower()

    # Check if app is supported
    if app not in APP_URLS:
        print(f"❌ Unknown app: {app}")
        print(f"Supported apps: {', '.join(APP_URLS.keys())}")
        return False

    app_url = APP_URLS[app]

    print("=" * 80)
    print(f"🔐 MANUAL LOGIN SETUP FOR {app.upper()}")
    print("=" * 80)
    print(f"\nOpening browser to: {app_url}")
    print("\n📋 Instructions:")
    print("1. A browser window will open")
    print("2. Manually log in to your account (using OAuth/SSO if required)")
    print("3. Wait until you see the main app interface")
    print("4. Return to this terminal and press Enter")
    print("5. The session will be saved for future use")
    print("\n⚠️  Do NOT close the browser window until prompted!")
    print("=" * 80)

    input("\nPress Enter to open browser...")

    # Create persistent browser (not headless for manual login)
    # The PersistentBrowserAgent automatically saves sessions!
    browser = PersistentBrowserAgent(
        headless=False,
        session_name=app
    )

    try:
        # Start the browser with context manager
        with browser:
            # Navigate to app
            print(f"\n🌐 Navigating to {app_url}...")
            browser.goto(app_url)

            # Wait for user to complete login
            print("\n⏳ Waiting for you to complete login...")
            print("   Take your time to:")
            print("   - Complete OAuth/SSO flow")
            print("   - Handle any 2FA if needed")
            print("   - Wait for the main app to fully load")

            input("\n✅ Press Enter once you're logged in and the app has loaded...")

            # Session is automatically saved by PersistentBrowserAgent
            print("\n💾 Session automatically saved!")
            print(f"   Session location: browser_sessions/{app}/")
            print(f"\n✅ SUCCESS! You can now run workflows without manual login:")
            print(f"   python run_workflow.py \"How do I create a project in {app}?\" --use-session")

        return True

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_sessions():
    """List all saved sessions"""
    print("\n" + "=" * 80)
    print("📂 SAVED SESSIONS")
    print("=" * 80)

    sessions_dir = Path("./browser_sessions")

    if not sessions_dir.exists():
        print("\nNo saved sessions found.")
        print("\nTo create a session, run:")
        print("  python setup_login.py <app_name>")
        print("\nExample:")
        print("  python setup_login.py asana")
    else:
        session_folders = [d for d in sessions_dir.iterdir() if d.is_dir()]

        if not session_folders:
            print("\nNo saved sessions found.")
        else:
            print(f"\nFound {len(session_folders)} session(s):\n")
            for folder in session_folders:
                # Calculate folder size
                size = sum(f.stat().st_size for f in folder.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                print(f"  ✅ {folder.name:<15} ({size_mb:.2f} MB)")
                print(f"     Location: {folder}")

    print("=" * 80 + "\n")


def clear_session(app: str):
    """Clear a saved session"""
    import shutil

    session_dir = Path(f"./browser_sessions/{app}")

    if session_dir.exists():
        shutil.rmtree(session_dir)
        print(f"✅ Cleared session for {app}")
        print(f"   Deleted: {session_dir}")
    else:
        print(f"⚠️  No session found for {app}")


def main():
    parser = argparse.ArgumentParser(
        description='Setup manual login sessions for OAuth/SSO apps'
    )

    parser.add_argument(
        'app',
        nargs='?',
        help='App name (asana, linear, notion, etc.)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all saved sessions'
    )

    parser.add_argument(
        '--clear',
        type=str,
        help='Clear saved session for specified app'
    )

    args = parser.parse_args()

    # Handle different modes
    if args.list:
        list_sessions()
    elif args.clear:
        clear_session(args.clear)
    elif args.app:
        setup_login_for_app(args.app)
    else:
        parser.print_help()
        print("\n" + "=" * 80)
        print("💡 QUICK START")
        print("=" * 80)
        print("\n1. Setup login for an app (e.g., Asana):")
        print("   python setup_login.py asana")
        print("\n2. Run a workflow using the saved session:")
        print("   python run_workflow.py \"How do I create a project in Asana?\" --use-session")
        print("\n3. List saved sessions:")
        print("   python setup_login.py --list")
        print("\n4. Clear a session:")
        print("   python setup_login.py --clear asana")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
