from flask import flash

from helpers.inventory_loader import delete_inventory_item
from helpers.db import get_db

def handle_delete(form):
    zone = form.get('zone')
    item_id = form.get('item_id')

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "DELETE FROM items WHERE id = %s AND zone = %s",
            (item_id, zone)
        )

        if cursor.rowcount > 0:
            flash(f"Deleted item from {zone}.", 'success')
        else:
            flash(f"Failed to delete item from {zone}. Item ID '{item_id}' not found in database.", 'error')
            