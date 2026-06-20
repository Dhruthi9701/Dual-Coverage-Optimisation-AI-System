"""
DuCO-Agent | Shared Utilities
src/utils/helpers.py

Common helper functions used across all agents.
Centralised here so nothing is duplicated across modules.
"""

import re
import json
import base64
from pathlib import Path


def to_number(value) -> float:
    """
    Safely coerce any money value to float.
    Handles: int, float, "350000", "Rs. 3,50,000", "₹3,50,000", None, ""
    Returns 0.0 if nothing numeric can be extracted.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", str(value))
    return float(cleaned) if cleaned else 0.0


def image_to_base64(path: Path) -> tuple[str, str]:
    """
    Read an image file and return (base64_string, media_type).
    Supports .png, .jpg, .jpeg
    """
    suffix = path.suffix.lower()
    media_type_map = {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return data, media_type


def load_state(state_path: Path) -> dict:
    """Load agent state from JSON file."""
    if not state_path.exists():
        raise FileNotFoundError(
            f"State file not found: {state_path}\n"
            "Run the pipeline in order: intake_agent -> cob_engine -> output_generator\n"
            "Or run: python main.py"
        )
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict, state_path: Path) -> None:
    """Save agent state to JSON file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def format_inr(amount) -> str:
    """Format a number as Indian Rupee string: 450000 -> 'Rs. 4,50,000'"""
    try:
        n = int(to_number(amount))
    except (ValueError, TypeError):
        return "Rs. 0"

    # Indian number formatting: last 3 digits, then groups of 2
    s = str(n)
    if len(s) <= 3:
        return f"Rs. {s}"
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return f"Rs. {result.lstrip(',')}"


def strip_json_fences(text: str) -> str:
    """Remove markdown code fences from LLM JSON responses."""
    return text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def parse_llm_json(text: str) -> dict:
    """Parse JSON from LLM response, stripping fences if present."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(strip_json_fences(text))
