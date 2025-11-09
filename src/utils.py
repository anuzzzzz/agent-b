"""Utility functions for state detection and comparison"""
import time
from typing import Dict, Any, Optional
from pathlib import Path
import json


def generate_state_id(description: str) -> str:
    """Generate a unique ID for a state"""
    timestamp = int(time.time() * 1000)
    clean_desc = description.lower().replace(" ", "_")
    return f"{clean_desc}_{timestamp}"


def save_metadata(
    screenshot_path: Path,
    state_info: Dict[str, Any],
    task: Optional[str] = None
) -> Path:
    """
    Save metadata JSON alongside screenshot
    
    Args:
        screenshot_path: Path to screenshot
        state_info: Dictionary with state information
        task: Optional task description
        
    Returns:
        Path to metadata file
    """
    metadata = {
        "screenshot": screenshot_path.name,
        "timestamp": int(time.time()),
        "state": state_info,
    }
    
    if task:
        metadata["task"] = task
    
    # Save as JSON with same name as screenshot
    metadata_path = screenshot_path.with_suffix('.json')
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Metadata saved: {metadata_path.name}")
    return metadata_path


def compare_dom_snapshots(snapshot1: Dict, snapshot2: Dict) -> bool:
    """
    Compare two DOM snapshots to detect significant changes
    
    Returns:
        True if significant change detected, False otherwise
    """
    # Simple comparison: check if element counts changed significantly
    if not snapshot1 or not snapshot2:
        return False
    
    count_diff = abs(snapshot1.get('element_count', 0) - snapshot2.get('element_count', 0))
    
    # If more than 5 new elements appeared, consider it significant
    return count_diff > 5


def wait_for_stability(page, timeout_ms: int = 2000):
    """
    Wait for page to be stable (no new network requests)
    
    Args:
        page: Playwright page object
        timeout_ms: How long to wait for stability
    """
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        # Additional small wait for animations
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"⚠️  Page may not be fully stable: {e}")