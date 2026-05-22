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
import pymysql
from flask import get_flashed_messages

#   global environmental functions
from utilities.login_token import token_flow      #   207 def login link -> 
from utilities.scan_skus import scanner_flow      #   this should lead to sorting with api
from utilities.inv_prod import append_to_json, inv_prod_flow      #   This should be the basic storage access
from utilities.delidocdb import sql_flow, db_manager, logger      #   This should be the basic db access

from routes.auth_routes import auth

from utilities.interact_json import select_json_file, load_json_data, save_json_data, update_inventory_item, delete_inventory_item, get_inventory_with_ids
#   from now import time_flow
#   from file_reader import select_flow, load_flow, get, save, append, update 
#   from json import file_flow
#   from fin_meas import fin_flow

app = Flask(__name__)
app.secret_key = os.urandom(24)  # CSRF protection
app.register_blueprint(auth)  # Register auth routes
cnx = None
selected_json_path: Optional[str] = None

DATA_DIR = Path("data")
JSON_FILES_DIR = Path("json_files")
DATA_DIR.mkdir(exist_ok=True)

#   Variables
storage_types = ["Freezer", "Fridge", "Dry"]
DATA_ZONES = {'freezer': [], 'fridge': [], 'dry': []}
item_types = ["Consumable", "Unconsumable"]
value_levels = ["High", "Mid", "Low"]
next_id = 4

def select_json(directory):
    return select_json_file(directory)

def load_delivery_data(filepath, default):
    load_delivery_data = load_json_data(filepath, default)
    return load_delivery_data

# def load_json(filename, {z: [] for Z in DATA_ZONES}):
#     load_json = load_json_data(filename, {z: [] for Z in DATA_ZONES})
#     return load_json

'''     Reused Code     '''
def save_delivery_data(filepath, data):
    save_json_data(filepath, data)
    return True

def save_json(filepath, data):
    save_json_data(filepath, data)
    return True

def get_delivery_order(filename):
    get_delivery = get_inventory_with_ids(filename)
    return get_delivery

def get_inventory(filename):
    get_complete_inventory = get_inventory_with_ids(filename)
    return get_complete_inventory

def update_delivery_order(filename, zone, item_id, new_name):
    update_delivery = update_inventory_item(filename, zone, item_id, new_name)
    return update_delivery
    
def update_inventory(filename, zone, item_id, new_name):
    update_inventory = update_inventory_item(filename, zone, item_id, new_name)
    return update_inventory

def append_to_delivery(new_data, filename):
    json_append = append_to_json(new_data, filename)
    return json_append

#   add new_item to json file
def append(new_data, filename):
    json_append = append_to_json(new_data, filename)
    return json_append

def delete_delivery_item(filename, zone, item_id):
    delete_delivery = delete_inventory_item(filename, zone, item_id)    
    return delete_delivery

def delete_inventory_item(filename, zone, item_id):
    delete_inventory = delete_inventory_item(filename, zone, item_id)
    return delete_inventory

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
    return render_template('dash_template.html')

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
    filename = DATA_DIR / "delivery.json"

    if request.method == 'POST':
        handle_scanner_post(request.form, filename)
    delivery = get_inventory_with_ids(filename)
    return render_template('scanner_template.html', delivery=delivery)

@app.route('/api')
def api():
    title_text = "API Endpoint"
    body_html = "<h1>🔌 API for inventory and delivery management</h1>"
    use_body = Markup(body_html)
    return render_template('api_template.html')

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
    return render_template('finance_template.html')

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
    return render_template(
        'zone_template.html',
        zones_html=zones_html,
        zones_display=zones_display,
        inventory=inventory)

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
    
    return render_template('time_frame_template.html', orders_html=orders_html)

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
        
        return render_template('contacts_template.html')
    except Exception:
        return render_template('contacts_template.html', titleText="Contacts", 
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



































