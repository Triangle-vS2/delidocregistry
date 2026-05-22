#   imports 
import os, json, time, random, logging, uuid
from pathlib import Path
from typing import Optional, Dict, Any, List


#   functions
def select_json_file(directory: str) -> str:
    """Select JSON file interactively with validation"""
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    json_files = [f for f in directory.iterdir() if f.suffix.lower() == '.json']
    if not json_files:
        raise ValueError(f"No .json files found in: {directory}")

    print(f"\nAvailable JSON files in {directory}:")
    for i, f in enumerate(json_files, 1):
        print(f"  {i}. {f.name}")

    while True:
        try:
            choice = input(f"\nSelect file [1-{len(json_files)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(json_files):
                return str(json_files[idx].resolve())
            print("Invalid choice")
        except ValueError:
            print("Please enter a number")
DATA_ZONES = ["freezer", "fridge", "dry"]

def load_json_data(filename: str, default: Dict[str, Any]) -> Dict[str, Any]:
    """Load JSON safely with fallback and enforced structure."""
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default.copy()

    # Enforce zone structure
    result = default.copy()
    for zone in DATA_ZONES:
        value = data.get(zone, [])
        result[zone] = value if isinstance(value, list) else []
    return result

def save_json_data(filepath: str, data: Dict[str, Any]):
    """Atomic JSON save."""
    tmp = filepath + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, filepath)


###     Reused Code     ###
def save_json_data(filepath: str, data: Dict[str, Any]):
    """Save JSON data atomically"""
    tmp_path = Path(filepath + '.tmp')
    try:
        with tmp_path.open('w') as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(filepath)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

def get_inventory_with_ids(filename: str) -> Dict[str, List[Dict]]:
    """Load inventory and ensure every item has a stable ID."""
    inventory = load_json_data(filename, {z: [] for z in DATA_ZONES})

    for zone, items in inventory.items():
        for i, item in enumerate(items):
            # Convert non-dict items
            if not isinstance(item, dict):
                item = {"name": str(item)}
                inventory[zone][i] = item

            # Add missing ID
            if "id" not in item:
                item["id"] = f"{zone}_{uuid.uuid4().hex}"

    return inventory

def update_inventory_item(filename: str, zone: str, item_id: str, new_name: str) -> bool:
    """Update an item's name while preserving all other fields."""
    inventory = get_inventory_with_ids(filename)

    if zone not in inventory:
        return False

    for item in inventory[zone]:
        if item.get("id") == item_id:
            item["name"] = new_name.strip()
            save_json_data(filename, inventory)
            return True

    return False


def delete_inventory_item(filename: str, zone: str, item_id: str) -> bool:
    """Delete an item by ID."""
    inventory = get_inventory_with_ids(filename)

    if zone not in inventory:
        return False

    before = len(inventory[zone])
    inventory[zone] = [item for item in inventory[zone] if item.get("id") != item_id]

    if len(inventory[zone]) != before:
        save_json_data(filename, inventory)
        return True

    return False
