"""Set-of-Marks (SoM) screenshot annotator for visual grounding"""
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import json


class SoMAnnotator:
    """
    Annotates screenshots with numbered marks for element grounding.

    Based on research from SeeAct (ICML 2024) and VisualWebArena.
    Overlays numbered boxes on interactive elements so LLM can refer to them by ID.
    """

    def __init__(self):
        self.mark_color = (255, 0, 0)  # Red
        self.text_color = (255, 255, 255)  # White
        self.box_color = (255, 0, 0)  # Red
        self.opacity = 180

    def annotate_screenshot(
        self,
        screenshot_path: Path,
        elements: List[Dict[str, Any]],
        output_path: Path = None
    ) -> Tuple[Path, Dict[int, Dict]]:
        """
        Annotate screenshot with numbered marks for each interactive element.

        Args:
            screenshot_path: Path to original screenshot
            elements: List of interactive elements with positions
            output_path: Where to save annotated image (optional)

        Returns:
            Tuple of (annotated_screenshot_path, element_mapping)
            element_mapping: {1: element_data, 2: element_data, ...}
        """
        # Load screenshot
        img = Image.open(screenshot_path)
        draw = ImageDraw.Draw(img, 'RGBA')

        # Try to load a font, fallback to default
        try:
            # Try to use a clear font
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            font = ImageFont.load_default()

        # Create element mapping
        element_mapping = {}

        # Annotate each element
        for idx, elem in enumerate(elements, start=1):
            pos = elem.get('position', {})
            x = pos.get('x', 0)
            y = pos.get('y', 0)
            width = pos.get('width', 0)
            height = pos.get('height', 0)

            # Skip elements with invalid positions
            if width <= 0 or height <= 0:
                continue

            # Draw bounding box around element
            box_coords = [x, y, x + width, y + height]
            draw.rectangle(box_coords, outline=self.box_color, width=2)

            # Draw numbered label
            label = str(idx)

            # Create a background box for the number
            # Get text size (approximate for default font)
            text_width = len(label) * 10 + 6
            text_height = 20

            label_x = x
            label_y = max(0, y - text_height - 2)  # Place above element

            # Draw label background
            label_box = [
                label_x,
                label_y,
                label_x + text_width,
                label_y + text_height
            ]
            draw.rectangle(label_box, fill=(*self.box_color, self.opacity))

            # Draw label text
            draw.text(
                (label_x + 3, label_y + 2),
                label,
                fill=self.text_color,
                font=font
            )

            # Store in mapping
            element_mapping[idx] = {
                'text': elem.get('text', ''),
                'role': elem.get('role', ''),
                'type': elem.get('type', ''),
                'position': pos,
                'selector': elem.get('selector', ''),
                'ariaLabel': elem.get('ariaLabel', '')
            }

        # Save annotated image
        if output_path is None:
            output_path = screenshot_path.parent / f"{screenshot_path.stem}_annotated.png"

        img.save(output_path)

        # Also save the mapping as JSON
        mapping_path = output_path.parent / f"{output_path.stem}_mapping.json"
        with open(mapping_path, 'w') as f:
            json.dump(element_mapping, f, indent=2)

        return output_path, element_mapping

    def create_element_list_text(self, element_mapping: Dict[int, Dict]) -> str:
        """
        Create a text summary of elements for LLM context.

        Args:
            element_mapping: Mapping from IDs to element data

        Returns:
            Formatted string listing all elements
        """
        lines = ["Available elements (numbered in screenshot):"]

        for elem_id, elem_data in element_mapping.items():
            text = elem_data.get('text', '')[:50]  # Limit text length
            role = elem_data.get('role', 'element')

            if text:
                lines.append(f"  [{elem_id}] {role}: \"{text}\"")
            else:
                lines.append(f"  [{elem_id}] {role}")

        return "\n".join(lines)
