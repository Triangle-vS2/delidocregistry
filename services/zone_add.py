import time
from flask import flash

from helpers.inventory_loader import get_inventory_with_ids, save_json_data
from helpers.zone_map import ZONE_MAP
from helpers.db import get_db

def handle_add(form):
    zone = form.get('zone')
    category = form.get('category', '')
    value_code = form.get('value', '')
    item = form.get('item', '')

    sku = f"{category}_{value_code}"
    db = get_db()

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM items WHERE name = %s AND zone = %s", (item, zone))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("UPDATE items SET count = count + 1 WHERE id = %s", (existing['id'],))
            db.commit()
            flash(f"Item '{item}' already exists in {zone} x{existing['count'] + 1}. Incremented count.", 'info')
            return

    new_id = f"{sku}_{int(time.time())}"
    cursor.execute("INSERT INTO items (id, sku, name, count, zone, category, value_code) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                   (new_id, sku, item, 1, zone, category, value_code)
    )

    flash(f"Added '{item}' to {zone} in zone {ZONE_MAP.get(zone, 'Unknown')}.", 'success')

