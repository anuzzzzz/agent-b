# Session Persistence for OAuth/SSO Apps

## Problem

Many modern web apps (like Asana, Notion, Linear) use OAuth or SSO (Single Sign-On) for authentication. These cannot be automated with simple email/password forms because:

- They redirect to third-party login providers (Google, Microsoft, etc.)
- They use complex authentication flows
- They may require 2FA or other security measures

## Solution

This project implements **browser session persistence** - saving and reusing authenticated browser sessions across workflow runs.

## How It Works

1. **Manual Login Once**: You log in manually through a real browser window
2. **Session Saved**: Your browser cookies and localStorage are saved to a file
3. **Session Reused**: Future workflow runs load the saved session, bypassing login

## Setup Instructions

### Step 1: Setup Login for Your App

Run the setup script to manually log in and save your session:

```bash
# For Asana (with Google OAuth)
python setup_login.py asana

# For Linear
python setup_login.py linear

# For Notion
python setup_login.py notion
```

**What happens:**
1. A browser window opens to the app's login page
2. You manually complete the OAuth/SSO login flow
3. Wait for the app to fully load
4. Press Enter in the terminal
5. Your session is saved to `data/sessions/<app>_session.json`

### Step 2: Run Workflows with Session

Now you can run workflows using the saved session:

```bash
# Use --use-session flag
python run_workflow.py "How do I create a project in Asana?" --use-session
```

The workflow will:
- Load your saved session (cookies + localStorage)
- Skip the login flow entirely
- Start directly on the authenticated app

## Managing Sessions

### List Saved Sessions

```bash
python setup_login.py --list
```

Shows all saved sessions with file sizes.

### Clear a Session

```bash
python setup_login.py --clear asana
```

Deletes the saved session file. You'll need to run setup again.

### When Sessions Expire

Sessions can expire after some time (varies by app). If you see:

```
⚠️  Session exists but authentication still required
   Your saved session may have expired.
   Run: python setup_login.py asana
```

Simply re-run the setup to create a fresh session.

## Session Files

Sessions are stored in: `data/sessions/<app>_session.json`

Each file contains:
- **Cookies**: Authentication tokens, session IDs
- **localStorage**: App-specific state and preferences
- **Metadata**: Session name and timestamp

**Security Note**: These files contain authentication data. Keep them private:
- Already gitignored in `.gitignore`
- Never commit to version control
- Treat like passwords

## Usage Examples

### Single Workflow with Session

```bash
python run_workflow.py "How do I create a project in Asana?" --use-session
```

### Batch Workflows with Session

```bash
python run_workflow.py --batch queries.txt --use-session
```

### Without Session (Public Pages)

```bash
python run_workflow.py "How do I search Wikipedia?" --no-auth
```

## Architecture

### Classes

**`PersistentBrowserAgent`** (extends `BrowserAgent`)
- Saves cookies and localStorage to JSON files
- Loads saved sessions on initialization
- Per-app session management

**`EnhancedWorkflowEngine`**
- New `use_session` parameter
- Automatically uses `PersistentBrowserAgent` when `--use-session` is set
- Skips authentication flow if session is valid

### Files Created

- `src/persistent_browser.py` - Session management class
- `setup_login.py` - Interactive login setup tool
- `data/sessions/` - Directory for session storage

## Troubleshooting

### "Session exists but authentication still required"

Your session has expired. Re-run setup:
```bash
python setup_login.py asana
```

### "Could not restore localStorage"

This is usually harmless. Cookies alone are often sufficient for authentication.

### Session Not Working

Try:
1. Clear the session: `python setup_login.py --clear asana`
2. Re-setup: `python setup_login.py asana`
3. Make sure to wait for the app to fully load before pressing Enter

### Browser Opens But Doesn't Navigate

Check your internet connection and the APP_URLS in `src/config.py`.

## Benefits

- ✅ Works with OAuth/SSO (Google, Microsoft, etc.)
- ✅ Supports 2FA and complex login flows
- ✅ No need to store third-party credentials
- ✅ Sessions persist across multiple workflow runs
- ✅ One-time manual setup per app

## Comparison with auth_manager.py

| Feature | auth_manager.py | Session Persistence |
|---------|----------------|---------------------|
| Email/Password Login | ✅ Yes | ❌ No need |
| OAuth/SSO Login | ❌ Cannot automate | ✅ Yes |
| 2FA Support | ❌ No | ✅ Yes |
| Manual Setup | ❌ No | ✅ Once per app |
| Session Reuse | ❌ No | ✅ Yes |

## When to Use Each Method

**Use Session Persistence** (`--use-session`):
- Apps with OAuth/SSO (Asana, Linear, Notion)
- Apps with 2FA enabled
- When you want to avoid storing credentials

**Use auth_manager.py** (default):
- Apps with simple email/password login
- Apps without OAuth
- Testing on public pages

**Use Neither** (`--no-auth`):
- Public websites (Wikipedia, Example.com)
- No authentication required
