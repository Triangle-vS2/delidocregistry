import json
from helpers.db import get_db

def get_inventory():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM items")
        rows = cursor.fetchall()

    inventory = {"freezer": [], "fridge": [], "dry": [], "other": []}
    for row in rows:
        inventory[row["zone"]].append(row)

    return inventory

def save_json_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def update_inventory_items(filename, zone, item_id, new_name):
    data = get_inventory_with_ids(filename)
    for item in data[zone]:
        if item['id'] == item_id:
            item['name'] = new_name
            save_json_data(filename, data)
            return True
    return False

def delete_inventory_item(filename, zone, item_id):
    data = get_inventory_with_ids(filename)
    before = len(data[zone])
    data[zone] = [item for item in data[zone] if item['id'] != item_id]
    save_json_data(filename, data)
    return len(data[zone]) < before
