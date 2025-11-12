"""Test SoM annotation on an existing screenshot"""
from pathlib import Path
from src.som_annotator import SoMAnnotator
from PIL import Image

# Create annotator
annotator = SoMAnnotator()

# Create test elements with positions
test_elements = [
    {
        'text': 'Projects',
        'role': 'button',
        'type': 'button',
        'position': {'x': 100, 'y': 50, 'width': 80, 'height': 30},
        'selector': 'button[aria-label="Projects"]',
        'ariaLabel': 'Projects'
    },
    {
        'text': 'Search',
        'role': 'button',
        'type': 'button',
        'position': {'x': 200, 'y': 50, 'width': 60, 'height': 30},
        'selector': 'button[aria-label="Search"]',
        'ariaLabel': 'Search'
    },
    {
        'text': 'Create',
        'role': 'button',
        'type': 'button',
        'position': {'x': 300, 'y': 50, 'width': 60, 'height': 30},
        'selector': 'button[aria-label="Create"]',
        'ariaLabel': 'Create'
    },
]

# Find an existing screenshot
screenshot_path = Path("data/screenshots/asana/view_projects_1762900020/01_dropdown_1762900028.png")

if screenshot_path.exists():
    print(f"Testing SoM annotation on: {screenshot_path}")

    # Annotate
    annotated_path, element_mapping = annotator.annotate_screenshot(
        screenshot_path,
        test_elements,
        output_path=Path("test_annotated.png")
    )

    print(f"✓ Annotated screenshot saved to: {annotated_path}")
    print(f"✓ Element mapping saved")
    print(f"\nElement mapping:")
    for elem_id, elem_data in element_mapping.items():
        print(f"  [{elem_id}] {elem_data['role']}: {elem_data['text']}")

    # Test create_element_list_text
    element_list = annotator.create_element_list_text(element_mapping)
    print(f"\nElement list for LLM:")
    print(element_list)
else:
    print(f"Screenshot not found: {screenshot_path}")
