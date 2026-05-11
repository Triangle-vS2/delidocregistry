#!/usr/bin/env python3
# hdmi_night.py - Production-ready improved version

import os, json, time, random, logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup
import configparser, mysql.connector
from mysql.connector import Error
from flask import get_flashed_messages

#   global environmental functions
from login_token import token_flow      #   207 def login link -> 
from scan_skus import scanner_flow      #   this should lead to sorting with api
from inv_prod import inv_prod_flow      #   This should be the basic storage access
#   from now import time_flow
#   from file_reader import select_flow, load_flow, get, save, append, update 
#   from json import file_flow
#   from fin_meas import fin_flow


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # CSRF protection
cnx = None
selected_json_path: Optional[str] = None

DATA_DIR = Path("data")
JSON_FILES_DIR = Path("json_files")
DATA_DIR.mkdir(exist_ok=True)

#   Variables
storage_types = ["Freezer", "Fridge", "Dry"]
item_types = ["Consumable", "Unconsumable"]
value_levels = ["High", "Mid", "Low"]
next_id = 4

class DatabaseManager:
    """Database connection manager with connection pooling"""
    
    def __init__(self):
        self.connection = None
    
    @contextmanager
    def get_cursor(self):
        cursor = None
        try:
            if not self.connection or not self.connection.is_connected():
                self._connect()
            cursor = self.connection.cursor(prepared=True)
            yield cursor
            self.connection.commit()
        except Error as e:
            if cursor:
                cursor.close()
            logger.error(f"Database error: {e}")
            if self.connection and self.connection.is_connected():
                self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
    
    def _connect(self):
        config = configparser.ConfigParser()
        if not config.read('contacts.cfg'):
            raise RuntimeError("contacts.cfg not found")
        
        if 'database' not in config:
            raise RuntimeError("No [database] section in contacts.cfg")
        
        db_config = config['database']
        self.connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['pass'],
            database=db_config['db'],
            autocommit=False
        )
        logger.info("✓ Database connected")
    
    def execute_query(self, query: str, params=None) -> List[tuple]:
        """Execute query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()


db_manager = DatabaseManager()


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

def load_delivery_data(delivery_filepath: str, default: Dict[str, Any]) -> Dict[str, Any]:
    """Load JSON data with fallback"""
    try:
        with open(delivery_filepath, 'r') as f:
            data = json.load(f)
            result = default.copy()
            for k, v in data.items():
                if k in result:
                    result[k] = v if isinstance(v, list) else []
            return result
    except (json.JSONDecodeError, FileNotFoundError):
        return default


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
def save_delivery_data(delivery_filepath: str, data: Dict[str, Any]):
    """Save JSON data atomically"""
    tmp_path = Path(delivery_filepath + '.tmp')
    try:
        with tmp_path.open('w') as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(delivery_filepath)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
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
def get_delivery_order(delivery_filename: str) -> Dict[str, List[Dict]]:
    delivery = load_delivery_data(delivery_filename, {'freezer': [], 'fridge': [], 'dry': []})
    for zone in delivery:
        zone_items = delivery[zone]
        if not isinstance(zone_items, list):
            print(f"Warning: {zone} is not a list ({type(zone_items)}), resetting to []")
            zone_items = []
            delivery[zone] = zone_items
            for i, item in enumerate(zone_items):
                if not isinstance(item, dict) or 'id' not in item:
                    delivery[zone][i] = {'id': f"{zone}_{i}_{int(time.time())}", 'name': str(item)}
    return delivery
def get_inventory_with_ids(filename: str) -> Dict[str, List[Dict]]:
    '''Load auto id for edits'''
    inventory = load_json_data(filename, {'freezer': [], 'fridge': [], 'dry': []})
    for zone in inventory:
        zone_items = inventory[zone]
        if not isinstance(zone_items, list):
            print(f"Warning: {zone} is not a list ({type(zone_items)}), resetting to []")
            zone_items = []
            inventory[zone] = zone_items
#   i is count
            for i, item in enumerate(zone_items):
                if not isinstance(item, dict) or 'id' not in item:
#   for item in inventory check sku and pair it with where it should go
#   time is where sku should be
                    inventory[zone][i] = {'id': f"{zone}_{i}_{int(time.time())}", 'name': str(item)}
    return inventory
def update_delivery_order(delivery_filename: str, zone: str, item_id: str, new_name: str):
    delivery = load_delivery_data(delivery_filename, {"freezer": [], "fridge": [], "dry": []})
    if zone in delivery:
        for i, item in enumerate(delivery[zone]):
            if isinstance(item, dict) and item.get('id') == item_id:
                delivery[zone][i] = {'id': item_id, 'name': new_name.strip()}
                save_json_data(delivery_filename, delivery)
                return True
        return False
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

def append_to_delivery(new_data: dict, delivery_filename: str) -> None:
    try:
        with open(delivery_filename, 'r+', encoding='utf-8') as file:
            file_data = json.load(file)
            if isinstance(file_data, dict) and 'items' in file_data:
                file_data['items'].append(new_data)
            else:
                raise ValueError('Expected "items" key in JSON structure.')
            file.seek(0)
            json.dump(file_data, file, indent=4)
            file.truncate()
    except FileNotFoundError:
        with open(delivery_filename, 'w', encoding='utf-8') as file:
            json.dump({'items': [new_data]}, file, indent=4)

#   add new_item to json file
def append_to_json(new_data: dict, filename: str) -> None:
    try:
        with open(filename, 'r+', encoding='utf-8') as file:
            file_data = json.load(file)
            if isinstance(file_data, dict) and 'items' in file_data:
                file_data['items'].append(new_data)
            else:
                raise ValueError('Expected "items" key in JSON structure.')
            file.seek(0)
            json.dump(file_data, file, indent=4)
            file.truncate()
    except FileNotFoundError:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump({'items': [new_data]}, file, indent=4)

def delete_delivery_item(delivery_filename: str, zone: str, item_id: str):
    ''''Delete item'''
    delivery = load_delivery_data(delivery_filename, {"freezer": [], "fridge": [], "dry": []})
    if zone in delivery:
        delivery[zone] = [item for item in delivery[zone] if not (isinstance(item, dict) and item.get('id') == item_id)]
        save_json_data(delivery_filename, delivery)
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

def flash_messages():
    """Render flash messages"""
    
    messages = get_flashed_messages(with_categories=True)
    if not messages:
        return ""
    return Markup("".join(
        f'<div style="padding: 10px; margin: 10px 0; border-radius: 4px; '
        f'background: {"#d4edda" if cat=="success" else "#f8d7da"}; '
        f'color: {"#155724" if cat=="success" else "#721c24"};">{msg}</div>'
        for cat, msg in messages
    ))


# Routes
"""  Move to bottom   """
@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


""" This is the home / page -->  |   move about to here  """

@app.route('/dash', methods=['GET'])
def index():
    """Main dashboard with navigation move to another file to make it cleaner"""
    return render_template('dash_template.html',
                         titleText="Dashboard",
                         bodyText=Markup(f"""
    <div style="font-family: Arial; max-width: 800px; margin: 20px auto;">
        <h1>📊 Dashboard</h1>
        <p><strong>Selected JSON:</strong> {selected_json_path or 'None'}</p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 20px 0;">
            <a href="/" style="padding: 15px; background: #fce4ec; text-decoration: none; border-radius: 8px; text-align: center;">👥 Login</a>
            <a href="/now" style="padding: 15px; background: #fff3e0; text-decoration: none; border-radius: 8px; text-align: center;">⏰ Time</a>
            <a href="/zone" style="padding: 15px; background: #e3f2fd; text-decoration: none; border-radius: 8px; text-align: center;">🧊 Zone Inventory</a>
            <a href="/scanner" style="padding: 15px; background: #fce4ec; text-decoration: none; border-radius: 8px; text-align: center;">📈 Scan Skus</a>
            <a href="/api" style="padding: 15px; background: #e3f2fd; text-decoration: none; border-radius: 8px; text-align: center;">🧊 Order</a>
            <a href="/time_frame" style="padding: 15px; background: #f3e5f5; text-decoration: none; border-radius: 8px; text-align: center;">📈 Time Frame</a>
            <a href="/contacts" style="padding: 15px; background: #e8f5e8; text-decoration: none; border-radius: 8px; text-align: center;">👥 Contacts</a>
            <a href="/about" style="padding: 15px; background: #fce4ec; text-decoration: none; border-radius: 8px; text-align: center;">ℹ️ About</a>
        </div>
    </div>
    """))
'''
#   Create a secure login using tokens to show user specific content
Create a secure site that puts the app behind security protection
Add some input checks to prevent injection
'''

""" This is the /login page --> |   Move to top this should be pointed at from the global variable """

# @app.route('/', methods=['POST'])
'''#   Currently there is an error from post going back to get 
One potential fix could be separating the two sites. 
This would create unneccessary redundancy.
Another fix would be to use vue to redirect the page
'''
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('user', '').strip()     #   Why is this here; web req
        result = token_flow()
        if result:
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        flash("Invalid credentials", "error")
    
    # filename = DATA_DIR / "home_page.json"

    # user_profiles = load_json_data(str(filename), {"session": [], "user": [], "token": [], "cookies": []})
    
    return render_template('login.html', titleText="Login",
        bodyText=Markup(f"""
        <div style="max-width:600px;margin:20px auto;">
            <h2>🧊 Login Page </h2>
            {flash_messages()}
            
            <form method="post" style="margin:20px 0;padding:15px;background:#f0f8ff;border-radius:8px;">
                <input type="hidden" name="action" value="add">
                <div style="display:flex;gap:10px;align-items:end;flex-wrap:wrap;">
                    <select name="user" style="padding:8px;flex:1;min-width:120px;">
                        <option value="member">Member</option>
                        <option value="supplier">Supplier</option>
                        <option value="manager">Manager</option>
                    </select>
                    <select name="permissions" style="padding:8px;flex:1;min-width:120px;">
                        <option value="read">Read</option>
                        <option value="write">Write</option>
                    </select>
                    <select name="value" style="padding:8px;flex:1;min-width:120px;">
                        <option value="a">High</option>
                        <option value="b">mid</option>
                        <option value="c">Low</option>
                    </select>
                    <input name="item" placeholder="User name" style="padding:8px;flex:2;min-width:200px;" required>
                    <button type="submit" style="padding:10px 20px;background:#2196f3;color:white;border:none;border-radius:4px;">➕ Add User</button>
                    <post redirect get>
                </div>
            </form>
            <body>
                <img src="{{ url_for('static', filename='shoes.jpg') }}" alt="shoes Image">
            </body>
        </div>"""))
'''
This is for delivery orders that refreshes the tmp json file and updates the main const json
#   api through skus for organization make compatible
move code to a separate file 
The scanner could identify anomalies; 
when reading json data it should standardize 
then trim to verify that the file is compatible 
'''
@app.route('/scanner', methods=['GET', 'POST'])
def scanner():
#   Scan the tmp json file that acts as the delivery order is it for export or import
    begin_scan = scanner_flow()
    # print (begin_scan)

    '''tmp'''
    # try:
    #     return zone_template
    # except Exception as e:
    #     import traceback
    #     return f"Error: {str(e)}<br>{traceback.format_exc()}", 500
    """ Zone inventory: add/edit/delete items with live tables. """


    delivery_filename = str(DATA_DIR / "delivery.json")
    
    # Handle POST actions
    if request.method == 'POST':
        action = request.form.get('action')
        delivery_direction = request.form.get('delivery_direction', '')
        category = request.form.get('category', '')
        abc_value = request.form.get('value', '').strip()
        zone_name = request.form.get('zone', '').strip()
        item = request.form.get('item', '').strip()
        # count_var += 1
        delivery = get_delivery_order(delivery_filename)
        

#   add a sku value to items as well as count available in inventory
#   sku will make it easier to filter in db
#   each item in json should be saved with a sku, (reiterates the id in human readable format) item name, location, and count
        if action == 'add' and zone_name in ['freezer', 'fridge', 'dry'] and item:
            sku = f"{category}_{abc_value}_{random.randint(1000,9999)}"
            item_exists = False
            for existing_item in delivery[zone_name]:
                if existing_item.get('name', '').lower() == item.lower():
                    existing_item['count'] = existing_item.get('count', 0) + 1
                    item_exists = True
                    flash(f" {item} -> x{existing_item['count']}", 'success')
                    break
            if not item_exists:
#   add item and reset counter
                new_item = {
                    'id': f"{sku}_{int(time.time())}",
                    'sku': sku,  
                    'name': item, 
                    'count': 1,
                    'zone': zone_name,
                    'direction': delivery_direction
                    }
                delivery[zone_name].append(new_item)
#   if new_item is a product that is in stock increase count
#   elif add new_item to inventory
            # seek[0]
            
                flash(f"added new {item} x1)", 'success')
            # Add to stock.json
            save_delivery_data(delivery_filename, delivery)
            zone_map = {
                'freezer': {'code': 'c', 'location': 'Freezer'},
                'fridge': {'code': 'b', 'location': 'The Walk-in'},
                'dry': {'code': 'a', 'location': 'Dry'}
            }
            zone_info = zone_map.get(zone_name, {'code': 'e', 'location': zone_name.title()})
            date_str = time.strftime('%Y-%m-%d')
            sys_data = {
                'type': 'object', 'properties': {
                    'title': 'Order trajectory', 'subtitle': 'Auto-generated order',
                    'updated_at': date_str, 
                    'data': {'type': 'array', 'items': [{
                        'rank': 1, 'order_date': date_str, 'current_period': 'winter',
                        'zone': zone_info, 'product': item, 'product_count': 1, 'order_calc': 1
                    }]}
                }
            }
            append_to_delivery(sys_data, str(DATA_DIR / "delivery.json"))
            
        elif action == 'edit':
            item_id = request.form.get('item_id')
            if update_delivery_order(delivery_filename, zone_name, item_id, item):
                flash("✅ Updated!", 'success')
            else:
                flash("❌ Update failed", 'error')
        elif action == 'delete':
            item_id = request.form.get('item_id')
            if delete_delivery_item(delivery_filename, zone_name, item_id):
                flash("✅ Deleted!", 'success')
            else:
                flash("❌ Delete failed", 'error')
    
    # Build HTML - FIXED STRUCTURE
    delivery = get_delivery_order(delivery_filename)
    zones_html = ""  # Initialize!
    
    for zone_name, items in delivery.items():
        # FIXED: items_html is separate variable Copy format
        items_html = "".join(
            f"<tr><td>{item.get('name', 'Unknown')} <strong style='color:#4caf50'>(x{item.get('count', 1)})</strong> "
            f"<br><small>SKU: {item.get('sku', 'N/A')}</small></td>"
            f"<td><input value=\"{item.get('name', '')}\" style=\"width:120px;padding:4px;\" "
            f"onchange=\"updateItem('{zone_name}', '{item.get('id', 'no-id')}', this.value)\"></td>"
            f"<td><button onclick=\"deleteItem('{zone_name}', '{item.get('id', 'no-id')}')\" "
            f"style=\"padding:4px 8px;background:#f44336;color:white;border:none;border-radius:3px;\">🗑️</button></td>"
            f"<td><button onclick=\"exportItem('{zone_name}', '{item.get('id', 'no-id')}')\" "
            f"style=\"padding:4px 8px;background:#f44336;color:white;border:none;border-radius:3px;\">EXPORT</button></td>"
            f"<td><button onclick=\"importItem('{zone_name}', '{item.get('id', 'no-id')}')\" "
            f"style=\"padding:4px 8px;background:#f44336;color:white;border:none;border-radius:3px;\">IMPORT</button></td></tr>"
            for item in items
        ) or "<tr><td colspan='3' style='padding:20px;color:#444;'>Empty</td></tr>"
        
        # FIXED: Build complete zone table
        zones_html += f"""
        <div style="margin-bottom:30px;">
            <h3 style="color:#2196f3;">🧊 {zone_name.title()}</h3>
            <table style="width:100%;border-collapse:collapse;margin-bottom:15px;">
                <thead><tr style="background:#f5f5f5;">
                    <th style="padding:10px;border:1px solid #ddd;">Item</th>
                    <th style="padding:10px;border:1px solid #ddd;">Edit</th>
                    <th style="padding:10px;border:1px solid #ddd;">Action</th>
                    <th style="padding:10px;border:1px solid #ddd;">Direction</th>
                </tr></thead>
                <tbody>{items_html}</tbody>
            </table>
        </div>"""
    
    # Summary display
    zones_display = "".join(
        f"<div><strong>{k.title()}:</strong> {', '.join(item['name'] for item in v) or 'Empty'}</div>"
        for k, v in delivery.items()
    )
    return render_template('valid_template.html', data=begin_scan,
        titleText="Delivery Zone - Editable",
        bodyText=Markup(f"""
        <div style="max-width:600px;margin:20px auto;">
            <h2>🧊 Inventory Management</h2>
            {flash_messages()}
            
            <form method="post" style="margin:20px 0;padding:15px;background:#f0f8ff;border-radius:8px;">
                <input type="hidden" name="action" value="add">
                <div style="display:flex;gap:10px;align-items:end;flex-wrap:wrap;">
                    <select name="zone" style="padding:8px;flex:1;min-width:120px;">
                        <option value="freezer">Freezer</option>
                        <option value="fridge">Fridge</option>
                        <option value="dry">Dry</option>
                    </select>
                    <select name="category" style="padding:8px;flex:1;min-width:120px;">
                        <option value="consumable">Consumable</option>
                        <option value="unconsumable">Unconsumable</option>
                    </select>
                    <select name="value" style="padding:8px;flex:1;min-width:120px;">
                        <option value="a">Valuable</option>
                        <option value="b">mid</option>
                        <option value="c">Common</option>
                    </select>
                    <select name="delivery_direction" style="padding:8px;flex:1;min-width:120px;">
                        <option value="Import">Import</option>
                        <option value="Export">Export</option>
                    </select>
                    <select name="product_value" style="padding:8px;flex:1;min-width:120px;">
                        <option value="Import">Price</option>
                        <option value="Export">Tax</option>
                    </select>
                    <input name="item" placeholder="Item name" style="padding:8px;flex:2;min-width:200px;" required>
                    <button type="submit" style="padding:10px 20px;background:#2196f3;color:white;border:none;border-radius:4px;">➕ Add Item</button>
                </div>
            </form>
            <hr><div style="font-size:16px;">{zones_display}</div>
            {zones_html}
            
            <script>
            function updateItem(zone, itemId, newName) {{
                if (!newName.trim()) {{ alert('Name cannot be empty'); return; }}
                const form = document.createElement('form');
                form.method = 'POST'; form.style.display = 'none';
                form.innerHTML = `
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="zone" value="${{zone}}">
                    <input type="hidden" name="item_id" value="${{itemId}}">
                    <input type="hidden" name="item" value="${{newName}}">
                `;
                document.body.appendChild(form); form.submit();
            }}
            function deleteItem(zone, itemId) {{
                if (confirm('Delete permanently?')) {{
                    const form = document.createElement('form');
                    form.method = 'POST'; form.style.display = 'none';
                    form.innerHTML = `
                        <input type="hidden" name="action" value="delete">
                        <input type="hidden" name="zone" value="${{zone}}">
                        <input type="hidden" name="item_id" value="${{itemId}}">
                    `;
                    document.body.appendChild(form); form.submit();
                }}
            }}
            </script>
        </div>"""))

@app.route('/financial_sheet', methods=["GET", "POST"])
def financial_sheet():
    title_text = "10Q"
    body_html = "<h1>📈 financial data, options, futures, growth and hedging </h1>"
    finance = request.form.get("financial_forms")
    use_body = Markup(body_html)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "calculate":
            finance = request.form.get("financial_forms")
            financial_sheet = request.form.get("ledger")
            if finance and financial_sheet:
                financial_forms.setdefault(finance, []).append()


# Simplified routes
@app.route('/now', methods=["GET", "POST"])
def now():
    title_text = "Now; Current Time"
    body_html = "<h2>⏰ {time.strftime('%H:%M:%S %Z')}</h2>"
    zone = request.form.get("storage_types")
    use_body = Markup(body_html)
    global next_id
    if request.method =="POST":
        action = request.form.get("action")
        if action == "add":
            zone = request.form.get("storage_types")
            item_name = request.form.get("item") # item 
            if zone and item_name:
                storage_types.setdefault(zone, []).append({"id": next_id, "name": item_name}) # item
                next_id += 1
                flash("Added Successfully!", "success")
        elif action == "edit":
            zone = request.form.get("zone")
            item_id = int(request.form.get("item_id", 0)) # item
            new_name = request.form.get("item") # item
            if zone in storage_types:
                for item in storage_types[zone]: # item
                    if item["id"] == item_id: # item
                        item["name"] = new_name # item
                        flash("Item updated", "success") # item
                        break
        elif action == "delete":
            zone = request.form.get("zone")
            item_id = int(request.form.get("item_id", 0)) # item
            if zone in storage_types:
                storage_types[zone] = [i for i in storage_types[zone] if i["id"] != item_id] # item
                flash("Item deleted", "info") # item
            
        return redirect(url_for("zones_view"))
    
    # zones_display = ", ".join(f"{z} ({len(z)})" for z in storage_types) # item this is where it originally failed
    zones_display = ", ".join(f"{z} ({len(items)})" for z, items in storage_types.items())
    parts = []
    for z, items in storage_types.items(): # item
        parts.append(f"<h3>{z}</h3><ul>")
        for i in items: # item
            parts.append(
                f'<li>'
                f'<span id="item-{z}-{i["id"]}">{i["name"]} </span> ' # item
                f'<button onclick="updateItem(\'{z}\', {i["id"]}, ' # item
                f'prompt(\'New name:\', \'{i["name"]}\'))">Edit</button>'
                f"</li>"
            )
        parts.append("</ul>")
    zones_html = "".join(parts)

    flash("Loaded Successfully!", "success")
    return render_template('now_template.html', 
                        zones_display=zones_display,
                        zones_html=zones_html,
                        titleText=title_text,
                        bodyText=use_body, #   this line has been changed to reroute the dash
                        storageTypes=list(storage_types.keys()),
                        itemTypes=item_types, # item
                        valueLevels=value_levels,
    )
    

'''
The functions of this route should be exported to inv_prod
split get and post into sep routes
this is the const inventory for the main warehouse
'''
@app.route('/zone', methods=['GET', 'POST'])
def zone():
    '''tmp'''
    # try:
    #     return zone_template
    # except Exception as e:
    #     import traceback
    #     return f"Error: {str(e)}<br>{traceback.format_exc()}", 500
    """Zone inventory: add/edit/delete items with live tables."""
    filename = str(DATA_DIR / "data.json")
    
    # Handle POST actions
    if request.method == 'POST':
        action = request.form.get('action')
        category = request.form.get('category', '')
        abc_value = request.form.get('value', '').strip()
        zone_name = request.form.get('zone', '').strip()    #   This accesses zone locations
        item = request.form.get('item', '').strip()
        # count_var += 1
        inventory = get_inventory_with_ids(filename)
        

#   add a sku value to items as well as count available in inventory
#   sku will make it easier to filter in db
#   each item in json should be saved with a sku, 
# (reiterates the id in human readable format) item name, location, and count
#   Change the zone variables to be specific to database
        if action == 'add' and zone_name in ['freezer', 'fridge', 'dry', 'other'] and item:
            sku = f"{category}_{abc_value}"
            item_exists = False
            for existing_item in inventory[zone_name]:
                if existing_item.get('name', '').lower() == item.lower():
#   How is this available for calculation
                    existing_item['count'] = existing_item.get('count', 0) + 1
                    new_calculation = existing_item['count'] + 1
                    item_exists = True
                    flash(f" {item} -> x{existing_item['count']}", 'success')
                    break
            if not item_exists:
#   add item and reset counter
                new_item = {
                    'id': f"{sku}_{int(time.time())}",
                    'sku': sku,  
                    'name': item, 
                    'count': 1,
                    'zone': zone_name
                    }
                inventory[zone_name].append(new_item)
#   if new_item is a product that is in stock increase count
#   elif add new_item to inventory
            # seek[0]
            
                flash(f"added new {item} x1)", 'success')
            # Add to stock.json
            save_json_data(filename, inventory)
#   This accesses zone locations
            zone_map = {
                'freezer': {'code': 'c', 'location': 'Freezer'},
                'fridge': {'code': 'b', 'location': 'The Walk-in'},
                'dry': {'code': 'a', 'location': 'Dry'},
                'other': {'code': 'd', 'location': 'other'}
            }
#   This refers to sorted locations
            zone_info = zone_map.get(zone_name, {'code': 'e', 'location': zone_name.title()})
            date_str = time.strftime('%Y-%m-%d')
            sys_data = {
                'type': 'object', 'properties': {
                    'title': 'Order trajectory', 'subtitle': 'Auto-generated order',
                    'updated_at': date_str, 
                    'data': {'type': 'array', 'items': [{
                        'rank': 1, 'order_date': date_str, 'current_period': 'winter',
                        'zone': zone_info, 'product': item, 'product_count': 1, 'order_calc': 1
                    }]}
                }
            }
            append_to_json(sys_data, str(DATA_DIR / "stock.json"))
            
        elif action == 'edit':
            item_id = request.form.get('item_id')
            if update_inventory_item(filename, zone_name, item_id, item):
                flash("✅ Updated!", 'success')
            else:
                flash("❌ Update failed", 'error')
        elif action == 'delete':
            item_id = request.form.get('item_id')
            if delete_inventory_item(filename, zone_name, item_id):
                flash("✅ Deleted!", 'success')
            else:
                flash("❌ Delete failed", 'error')
    
    # Build HTML - FIXED STRUCTURE
    inventory = get_inventory_with_ids(filename)
    zones_html = ""  # Initialize!
    
    for zone_name, items in inventory.items():
        # FIXED: items_html is separate variable
        items_html = "".join(
            f"<tr><td>{item.get('name', 'Unknown')} <strong style='color:#4caf50'>(x{item.get('count', 1)})</strong> "
            f"<br><b><small>SKU: {item.get('sku', 'N/A')}</small></b></td>"
            f"<td><mark><input value=\"{item.get('name', '')}\" style=\"width:120px;padding:4px;\" "
            f"onchange=\"updateItem('{zone_name}', '{item.get('id', 'no-id')}', this.value)\"></mark></td>"
            f"<td><button onclick=\"deleteItem('{zone_name}', '{item.get('id', 'no-id')}')\" "
            f"style=\"padding:4px 8px;background:#f44336;color:white;border:none;border-radius:3px;\">🗑️</button></td></tr>"
            for item in items
        ) or "<tr><td colspan='3' style='padding:20px;color:#444;'>Empty</td></tr>"
        
        # FIXED: Build complete zone table
        zones_html += f"""
        <div style="margin-bottom:30px;">
            <h3 style="color:#2196f3;">🧊 {zone_name.title()}</h3>
            <table style="width:100%;border-collapse:collapse;margin-bottom:15px;">
                <thead><tr style="background:#f5f5f5;">
                    <th style="padding:10px;border:1px solid #ddd;">Item description; \t part #101 or SKU | </th>
                    <th style="padding:10px;border:1px solid #ddd;">\t item; seat assembly | Edit</th>
                    <th style="padding:10px;border:1px solid #ddd;"> quantity required 1 | Action</th>
                </tr></thead>
                <tbody>{items_html}</tbody>
            </table>
        </div>"""
    
    # Summary display
    zones_display = "".join(
        f"<div><strong>{k.title()}:</strong> {', '.join(item['name'] for item in v) or 'Empty'}</div>"
        for k, v in inventory.items()
    )
#   Zone location is hard coded other elements like category could be improved
#   In the form I need an option that allows the user to choose if they want to add data
    return render_template('zone_template.html',
        titleText="Zone Inventory - Editable",
        bodyText=Markup(f"""
        <div style="max-width:600px;margin:20px auto;">
            <h2>🧊 Inventory Management</h2>
            {flash_messages()}
            
            <form method="post" style="margin:20px 0;padding:15px;background:#f0f8ff;border-radius:8px;">
                <input type="hidden" name="action" value="add">
                <div style="display:flex;gap:10px;align-items:end;flex-wrap:wrap;">
                    <select name="zone" style="padding:8px;flex:1;min-width:120px;">
                        <option value="freezer">Freezer</option>
                        <option value="fridge">Fridge</option>
                        <option value="dry">Dry</option>
                        <option value="other">other</option>
                    </select>
                    <select name="category" style="padding:8px;flex:1;min-width:120px;">
                        <option value="consumable">Consumable</option>
                        <option value="unconsumable">Unconsumable</option>
                        <option value="other">other</option>
                    </select>
                    <select name="value" style="padding:8px;flex:1;min-width:120px;">
                        <option value="a">Valuable</option>
                        <option value="b">mid</option>
                        <option value="c">Common</option>
                        <option value="other">other</option>
                    </select>
                    <input name="item" placeholder="Item name" style="padding:8px;flex:2;min-width:200px;" required>
                    <button type="submit" style="padding:10px 20px;background:#2196f3;color:white;border:none;border-radius:4px;">➕ Add Item</button>
                </div>
            </form>
            <hr><div style="font-size:16px;">{zones_display}</div>
            {zones_html}
            
            <script>
            function updateItem(zone, itemId, newName) {{
                if (!newName.trim()) {{ alert('Name cannot be empty'); return; }}
                const form = document.createElement('form');
                form.method = 'POST'; form.style.display = 'none';
                form.innerHTML = `
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="zone" value="${{zone}}">
                    <input type="hidden" name="item_id" value="${{itemId}}">
                    <input type="hidden" name="item" value="${{newName}}">
                `;
                document.body.appendChild(form); form.submit();
            }}
            function deleteItem(zone, itemId) {{
                if (confirm('Delete permanently?')) {{
                    const form = document.createElement('form');
                    form.method = 'POST'; form.style.display = 'none';
                    form.innerHTML = `
                        <input type="hidden" name="action" value="delete">
                        <input type="hidden" name="zone" value="${{zone}}">
                        <input type="hidden" name="item_id" value="${{itemId}}">
                    `;
                    document.body.appendChild(form); form.submit();
                }}
            }}
            </script>
        </div>"""))

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = []
    if query:
        try:
            results = db_manager.execute_query(
                "SELECT id, CONCAT(first, ' ', last) as name, email FROM contactsTable "
                "WHERE Phone_Number LIKE %s OR CONCAT(first, ' ', last) LIKE %s",
                (f'%{query}%', f'%{query}%')
            )
        except Exception:
            pass
    return render_template('search.html', results=results, query=query)


#   use this as a tool that can adjust for periods that have surplus or deficit 
"""  Add in average calculation   """

@app.route('/time_frame', methods=['GET', 'POST'])
def time_frame():
    filename = DATA_DIR / "stock.json"
    data = load_json_data(str(filename), [])
    
    message = ""
    if request.method == 'POST':
        try:
            prod = request.form.get('prod', '').strip()
            stock_order = int(request.form.get('stock_order', 0))
            variance = int(request.form.get('variance', 0))
            season = request.form.get('season', 'winter')
            
            order = stock_order - variance
            record = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'prod': prod, 'stock_order': stock_order, 'variance': variance,
                'order': order, 'season': season
            }
            data.append(record)
            save_json_data(str(filename), data[-100:])  # Keep last 100 records
            flash(f"Saved order for {prod}: {order}", 'success')
        except ValueError:
            flash("Please enter valid numbers", 'error')
    
    recent_orders = data[-5:]
    orders_html = "".join(
        f"<div style='padding: 8px; border-bottom: 1px solid #eee;'>{d['prod']}: "
        f"<strong>{d['order']}</strong> ({d['season']}) - {d.get('timestamp', 'N/A')}</div>"
        for d in reversed(recent_orders)
    ) or "<p>No orders yet</p>"
    
    return render_template('valid_template.html', titleText="Order Trajectory",
                         bodyText=Markup(f"""
    <div style="max-width: 600px; margin: 20px auto;">
        <h2>📈 Order Trajectory</h2>
        {flash_messages()}
        <form method="post" style="margin: 20px 0;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <input name="prod" placeholder="Product" required>
                <input type="number" name="stock_order" placeholder="Stock Order" required>
                <input type="number" name="variance" placeholder="Variance">
                <select name="season">
                    <option>winter</option><option>spring</option>
                    <option>summer</option><option>fall</option>
                </select>
            </div>
            <button type="submit" style="padding: 10px 20px; background: #4caf50; color: white; border: none; border-radius: 4px; margin-top: 10px;">Update Order</button>
        </form>
        <hr>
        <h3>Last 5 Orders</h3>
        <div>{orders_html}</div>
        <br><a href="/" style="color: #2196f3;">← Back to Dashboard</a>
    </div>
    """))

'''  Network   '''
@app.route('/contacts')
def contacts():
    try:
        contacts = db_manager.execute_query(
            "SELECT id, CONCAT(first, ' ', last) as name FROM contactsTable ORDER BY id"
        )
        contacts_html = "".join(
            f"<tr><td>{c[0]}</td><td><a href='/contactsDetail/{c[0]}'>{c[1]}</a></td></tr>"
            for c in contacts
        ) or "<tr><td colspan='2'>No contacts found</td></tr>"
        
        return render_template('contacts_template.html', titleText="Contacts",
                             bodyText=Markup(f"""
            <div style="max-width: 600px; margin: 20px auto;">
                <h2>👥 Contacts</h2>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr style="background: #f5f5f5;"><th>ID</th><th>Name</th></tr>
                    {contacts_html}
                </table>
                <input name="item" placeholder="Item name" style="padding:8px;flex:2;min-width:200px;" required>
                <br><a href="/" style="color: #2196f3;">← Back to Dashboard</a>
            </div>
            """))
    except Exception:
        return render_template('valid_template.html', titleText="Contacts", 
                             bodyText="Database unavailable")

'''   
Move to beginning  
The about page should have an html template that has contact information.
This would be a good time to include email, and linkedin
This is where a bio goes; describe the logic behind the app
'''

@app.route('/about')
def about():
    return render_template(
        'about_template.html',
        titleText="About",
        server_id=random.randint(1000, 9999)
    )

"""  
Run through port 443   | add more description 
"""

if __name__ == "__main__":
    print("🚀 Starting improved Flask app...")
    # Database (fails gracefully)
    try:
        db_manager._connect()
        logger.info(" Database connected")
    except Exception as e:
        logger.warning(f"Database unavailable: {e}")
    
    try:
        json_dir = str(DATA_DIR)
        json_files = list(DATA_DIR.glob("*.json"))
        if json_files:
            selected_json_path = str(json_files[0])
            logger.info(f" Selected JSON: {selected_json_path}")
        else:
            logger.warning("NO JSON files in data/ - scanner will fail")
    except Exception as e:
        logger.warning(f"JSON selection failed: {e}")

    port = int(os.environ.get('PORT', 5000))
    # debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    # Start server
    app.run(host='0.0.0.0', port=port, debug=True)
    # JSON selection
    # try:
    #     selected_json_path = select_json_file(r"C:/Users/beami/OneDrive/Desktop/info sec/data")
    #     logger.info(f"✓ Selected JSON: {selected_json_path}")
    # except Exception as e:
    #     logger.warning(f"✗ JSON selection failed: {e}")
    
    
    # logger.info("Server stopped")
