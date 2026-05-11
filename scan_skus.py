''' Supply Chain sorting algo 
'''
'''
Proposal; Using enumeration to organize skus. 
This script should read an order receipt and identify where to assign skus
To use the inventory management to extract an shipment of skus and 
sort it into convenient and efficient structure that can be retreived 
a manageable process that will overall improve the delivery. 

This should be reset each delivery for optimizing each load with current proj


scan a new tmp json file and sort it into the const inventory json

'''

#   Imports
import json, os, time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, unquote
import urllib
from typing import Optional, Dict, Any, List

INV_PROD = os.path.abspath('./data/data.json')
UTIL_JSON = os.path.abspath('./utilities/interact_json')
DOCS_COLLECTION = os.path.abspath('./json_files/data.json')
#   based on needs select shipment record
SHIPMENT_LOGS = os.path.abspath('./shipment_record/{}.json')

#   global env functions

# from UTIL_JSON import util_flow  -->

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

'''     Reused Code     '''
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

@dataclass
class Session:
    user: list[str]
    token: list[str]
    cookies: list[str]
#   Variables
company_dict: list[str] = []
extracted_data: list[str] = []
#   Functions
def create_folder_with_files(folder, files):
    try:
        os.makedirs(folder, exist_ok=True)
        print(f"folder '{folder}' created or already exosts.")
        for file_name in files:
            file_path = os.path.join(folder, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write(f"This is {file_name}\n")
                print(f"File '{file_name}' created.")
            else:
                print(f"File '{file_name}' already exists, skipping.")
    except OSError as e:
        print(f"Error creating folder or files: {e}")

def scan(selected_json_path):
    return

def append_to_json(extracted_data):
    data = ''
    new_data = ''
    filepath = 'temporary.tmp'
    with filepath.open('w') as f:
        try: 
            data = json.load(f)
        except json.JSONDecodeError:
            data = {'items': []}

    data['info'].append(new_data)
    f.seek(0)
    json.dump(data, f, indent=2)
    f.truncate()
    return


''' '''


def analyze_all_inventory():
    '''take the json_files folder as a shipment orders to sort and '''
    '''Utilize AI and big data models to create a neural network 
    that understands the layout and information that the company collects'''
    '''next steps; learn how to implement ai to adapt to the type of 
    information it is collecting (PyTorch)'''
    
    append_to_json(extracted_data)
    return
def translate_path(self, path):
    parsed = urlparse(path)
    path = parsed.path
    path = unquote(path)
#   define static data
#   insert a reader for current shipment 
    if path.startswith('/json_files'):
        path = path.replace('//', '/')
        rel_path = path[len('/analysis/docs/'):]
        return os.path.join(DOCS_COLLECTION, rel_path)
    elif path.startswith('/data/'):
        rel_path = path[len('/anaylsis/'):]
        return os.path.join(INV_PROD, rel_path)
    else:
        raise FileNotFoundError(f"File not found: {path}")
    return
def sorts_relative_data():
    '''Discuss with company managers what their current business model to modify how the data will be sorted'''
    
    filepath = 'temporary'
    tmp_path = Path(filepath + '.tmp')
    with tmp_path.open('w') as f:
        json.dump(extracted_data, f, indent=4)

    return

#   Main
def scanner_flow() -> Session:
    '''Create a session that identifies each sku of order
    then store in json directory
    this reads available data and creates a folder and sub file to place it in
    '''
    folder = "warehouse inventory"
    sub_files = ["file{n}.json", "file{n}.json", "notes.md"]
    create_folder_with_files(folder,sub_files)
    scan(select_json_file)
    return
if __name__ == "__main__":
    scanner_flow()