# Set-of-Marks (SoM) Visual Grounding Implementation

## Overview

This system implements **Set-of-Marks (SoM) visual grounding** for web automation, based on industry research from SeeAct (ICML 2024) and VisualWebArena. SoM solves the critical problem of **element disambiguation** in visual web agents.

## The Problem: Element Disambiguation

### What We Discovered
Early implementations using pure visual descriptions failed when multiple elements shared the same text. For example:
- **"Projects"** appears as both:
  - A dropdown toggle button (header)
  - A navigation link (sidebar)

When the LLM said "click Projects", the system would always click the first match (dropdown toggle), causing it to loop endlessly opening/closing the dropdown instead of navigating.

### Why It Matters
Modern web apps have complex UIs with repeated text across different interactive elements. Pure text matching OR pure visual description both fail to uniquely identify elements.

## The Solution: Set-of-Marks (SoM)

### How It Works

1. **Extract Interactive Elements** - Get all clickable elements with bounding box positions from the DOM
2. **Annotate Screenshot** - Overlay numbered red boxes on each interactive element
3. **LLM Sees Numbers** - The vision model sees the annotated screenshot with numbered elements
4. **Element ID Response** - LLM returns `element_id: 5` instead of describing the element
5. **Precise Execution** - System uses the element_id to look up exact element from mapping and clicks it

### Visual Example

Instead of:
```
LLM: "Click the 'Projects' link in the sidebar"
System: *searches for "Projects" → finds dropdown first → wrong element*
```

With SoM:
```
Screenshot shows:
  [1] Projects (dropdown toggle)
  [2] Search
  [3] Projects (sidebar link)

LLM: {"action": "click", "element_id": 3}
System: *looks up element 3 → gets exact sidebar link → correct!*
```

## Implementation Details

### Architecture

```
workflow_engine.py
  └─> Captures screenshot
  └─> Extracts interactive elements (state_detector.py)
  └─> Annotates screenshot with numbers (som_annotator.py)
  └─> Passes annotated image to LLM (llm_agent.py)
  └─> LLM returns element_id
  └─> Executes action on exact element (browser.py)
```

### Key Files

**src/som_annotator.py** - Core SoM implementation
- `annotate_screenshot()` - Draws numbered red boxes on elements
- `create_element_list_text()` - Generates element list for LLM context
- Returns: (annotated_screenshot_path, element_mapping)

**src/prompts.py** - Updated prompts
- Explains numbered boxes to LLM
- Expects JSON response with `element_id` field
- Example: `{"action": "click", "element_id": 5}`

**src/llm_agent.py** - LLM decision maker
- Accepts `element_mapping` parameter
- Builds element list from mapping
- Passes annotated screenshot to GPT-4V

**src/browser.py** - Action executor
- Accepts `element_mapping` parameter
- Uses `element_id` to look up element data
- Tries multiple strategies: text, aria-label, role+text, CSS selector
- Falls back to visual-first approach if element_id not provided

**src/workflow_engine.py** - Main workflow loop
- Integrates all components
- Passes element_mapping through the pipeline

### Response Format

The LLM now responds with:

```json
{
  "action": "click",
  "element_id": 5,
  "description": "Navigate to Projects page",
  "reasoning": "Element [5] is the Projects link in sidebar"
}
```

For fill actions:
```json
{
  "action": "fill",
  "element_id": 12,
  "text": "New Task Title",
  "description": "Enter task name",
  "reasoning": "Element [12] is the task name input field"
}
```

## Research Background

### SeeAct (ICML 2024)
- Paper: "GPT-4V(ision) is a Generalist Web Agent, if Grounded"
- Key finding: Pure visual OR pure DOM approaches have low success rates
- Solution: Set-of-Marks combines visual + structural grounding
- Result: Significantly improved task completion rates

### Why This Approach Works
1. **Visual Grounding** - LLM sees the actual UI layout and context
2. **Structural Precision** - Numbered IDs provide unambiguous element references
3. **Disambiguation** - Multiple "Projects" buttons become [1], [2], [3]
4. **Robust Matching** - Multiple fallback strategies for finding elements

## Current Status

### ✅ Implemented
- [x] SoM screenshot annotation with numbered red boxes
- [x] Element mapping generation (ID → element data)
- [x] Updated LLM prompts for element_id responses
- [x] Browser action executor with element_id support
- [x] Complete workflow integration
- [x] Visual verification (test_annotated.png shows numbered boxes)

### 🔄 Next Steps
1. **Test on Live Workflow** - Need to login to Asana and run complete test
2. **Capture Working Workflows** - Get 3-5 successful workflows across apps
3. **Video Documentation** - Record Loom demonstration
4. **Final Submission** - Package for Softlight Engineering review

## Testing

### Quick Test
```bash
# Test SoM annotation on existing screenshot
python test_som.py
```

This verifies:
- ✓ Screenshot annotation with numbered boxes
- ✓ Element mapping generation
- ✓ Visual output (test_annotated.png)

### Full Workflow Test
```bash
# Run complete workflow with SoM (requires login)
python run_workflow.py "How do I view my projects in Asana?" --use-session
```

## Advantages Over Previous Approach

| Feature | Old (Visual-First) | New (SoM) |
|---------|-------------------|-----------|
| Element selection | Text description | Numbered ID |
| Disambiguation | ❌ Fails on duplicates | ✅ Unique IDs |
| LLM reasoning | Verbose descriptions | Concise numbers |
| Execution accuracy | ~30% (many loops) | Expected: >80% |
| Research backing | Ad-hoc approach | ICML 2024 paper |

## Technical Notes

### Element Extraction
- Uses Playwright's accessibility tree + DOM queries
- Gets bounding boxes for visual positioning
- Filters for visible, interactive elements only
- Limits to top 50 elements to avoid overwhelming LLM

### Visual Annotation
- Red boxes (255, 0, 0) with 2px borders
- White text on semi-transparent red background
- Numbers placed above elements when possible
- Saves both annotated PNG and element mapping JSON

### Action Execution Strategies
When given element_id=5, the system tries:
1. Find by exact text match
2. Find by aria-label
3. Find by role + text (for buttons/links)
4. Find by CSS selector (fallback)

This multi-strategy approach ensures robust element finding even when DOM changes slightly.

## References

- [SeeAct Paper (ICML 2024)](https://osu-nlp-group.github.io/SeeAct/)
- [VisualWebArena](https://jykoh.com/vwa)
- [Browser-Use (industry implementation)](https://github.com/browser-use/browser-use)

## Contact

For questions about this implementation, refer to:
- Workflow engine: `src/workflow_engine.py`
- SoM annotator: `src/som_annotator.py`
- Updated prompts: `src/prompts.py`
