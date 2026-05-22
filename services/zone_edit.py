from flask import flash

from helpers.inventory_loader import update_inventory_item
from helpers.db import get_db

def handle_edit(form):
    zone_name = form.get('zone')
    item_id = form.get('item_id')
    new_name = form.get('item')

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("UPDATE items SET name = %s WHERE id = %s", (new_name, item_id))
        
        if cursor.rowcount > 0:
            flash(f"Updated item in {zone_name} to '{new_name}'.", 'success')
        else:
            flash(f"Failed to update item in {zone_name}. Item ID '{item_id}' not found.", 'error') 
