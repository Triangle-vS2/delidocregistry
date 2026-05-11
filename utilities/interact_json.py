#   imports 
import os, json, time, random, logging
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


def load_json_data(filepath: str, default: Dict[str, Any]) -> Dict[str, Any]:
    """Load JSON data with fallback"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            result = default.copy()
            for k, v in data.items():
                if k in result:
                    result[k] = v if isinstance(v, list) else []
            return result
    except (json.JSONDecodeError, FileNotFoundError):
        return default

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
    '''Load auto id for edits'''
    inventory = load_json_data(filename, {'freezer': [], 'fridge': [], 'dry': []})
    for zone in inventory:
        zone_items = inventory[zone]
        if not isinstance(zone_items, list):
            print(f"Warning: {zone} is not a list ({type(zone_items)}), resetting to []")
            zone_items = []
            inventory[zone] = zone_items
        for i, item in enumerate(zone_items):
            if not isinstance(item, dict) or 'id' not in item:
                inventory[zone][i] = {'id': f"{zone}_{i}_{int(time.time())}", 'name': str(item)}
    return inventory

def update_inventory_item(filename: str, zone: str, item_id: str, new_name: str):
    ''''update item'''
    inventory = load_json_data(filename, {"freezer": [], "fridge": [], "dry": []})
    if zone in inventory:
        for i, item in enumerate(inventory[zone]):
            if isinstance(item, dict) and item.get('id') == item_id:
                inventory[zone][i] = {'id': item_id, 'name': new_name.strip()}
                save_json_data(filename, inventory)
                return True
        return False
    
def delete_inventory_item(filename: str, zone: str, item_id: str):
    ''''Delete item'''
    inventory = load_json_data(filename, {"freezer": [], "fridge": [], "dry": []})
    if zone in inventory:
        inventory[zone] = [item for item in inventory[zone] if not (isinstance(item, dict) and item.get('id') == item_id)]
        save_json_data(filename, inventory)
        return True
    return False

def util_flow():
    return