# Agent B - Generalized Web Automation with Set-of-Marks

A visual grounding approach to web automation that works across any web application without hardcoding.

## Demo Video

**Watch the live demo**: [Loom Video](https://drive.google.com/file/d/1DNS_4GyoscAZgsndr6fHIzYAp8paDWbL/view?usp=sharing)

The video demonstrates Agent B automating tasks across Asana, Linear, and Notion in real-time.

## What It Does

Agent B automates web tasks by "seeing" the interface like a human would - using numbered visual markers on interactive elements. Instead of brittle CSS selectors or XPath, it uses a vision-language model to understand what's on screen and decide what to click next.

**Key Features:**
- Works across any web app (Asana, Notion, Linear, etc.) without app-specific code
- Handles popups, modals, and onboarding flows automatically
- Uses Set-of-Marks (SoM) visual grounding from ICML 2024 research
- Natural language task input: "Create a task called 'X' in Asana"
- Captures screenshots and workflow summaries for each run

## How It Works

1. **Query Parsing**: Extracts app name and task from natural language
2. **Browser Launch**: Opens authenticated browser session
3. **Visual Grounding**: Takes screenshot and annotates interactive elements with numbered red boxes
4. **LLM Decision**: Vision model sees the numbered elements and decides: "Click element [5]" or "Fill element [12] with 'text'"
5. **Execution**: Performs the action and captures state changes
6. **Iteration**: Repeats until task is complete

## Example Usage

```bash
# Create a task in Asana
python run_workflow.py "Create a task called 'Test SoM Implementation' in Asana" --use-session

# View projects in Linear
python run_workflow.py "View all projects in Linear" --use-session

# Add a page in Notion
python run_workflow.py "Create a page called 'Meeting Notes' in Notion" --use-session
```

## Architecture

- **Set-of-Marks (SoM) Annotation**: Numbered red boxes overlay interactive elements
- **Element Disambiguation**: Numbers eliminate ambiguity - "Click [19]" instead of "Click the button labeled 'Create'"
- **Multi-Strategy Element Finding**: Text match → ARIA labels → Role+text → CSS selectors
- **Generalized Popup Handling**: Automatically detects and dismisses blocking overlays
- **Persistent Sessions**: Saves browser state for OAuth/SSO apps

## Successful Workflows

Tested and working across multiple applications:

1. **Asana**: Create task (11 steps)
2. **Notion**: Create page (5 steps)
3. **Notion**: Add to-do item (10 steps)
4. **Linear**: View all projects (3 steps)

## Key Files

- `src/som_annotator.py` - Visual annotation with numbered red boxes
- `src/llm_agent.py` - LLM decision-making and element mapping
- `src/workflow_engine.py` - Orchestrates the full workflow
- `src/prompts.py` - Prompt engineering for task completion and popup handling
- `src/browser.py` - Playwright browser control

## Why This Approach?

Traditional web automation breaks when UIs change. By using visual grounding with numbered markers, Agent B:
- Adapts to UI changes without code updates
- Works across different apps with the same codebase
- Handles edge cases (popups, slow loads) like a human would
- Creates interpretable workflows (see exactly what the agent "saw")

## Output

Each workflow run generates:
- Annotated screenshots showing numbered elements at each step
- `workflow_summary.json` with action history and key states
- `workflow_metadata.json` with task details and configuration

---

Built for Softlight Engineering's Agent B take-home assignment.
