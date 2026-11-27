from email.policy import default

from flask import Blueprint, request, redirect, render_template, url_for, flash, get_flashed_messages
from markupsafe import Markup
import random, logging, psycopg2
from final_project import get_account, create_order, get_orders, get_historical_data, save_symbol_csv, create_csvs_for_symbols, compute_strategy_profit, sma_cs, mean_reversion_strategy, momentum_strategy, compare_all_strategies_for_all_symbols
from delivery_app import DatabaseManager    #   This should be the basic db access
# from services.backenddbsql import DatabaseManager
from helpers.db import build_summary, build_portfolio_summary


backend_site = Blueprint('backend_site', __name__)
logger = logging.getLogger(__name__)
db = DatabaseManager()


def create_inventory_items_table():
        with db.get_cursor() as cursor:
            cursor.execute(f"postgresql://admin:lVZqlZ3q1ldXW3BeNcZSBCTS20E2xr2U@dpg-dc3qec59el5s739au87g-a/circlesqldata;")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name VARCHAR(255),
                count INT DEFAULT 1,
                zone_id INT,
                category VARCHAR(64),
                value_level VARCHAR(16),
                sku VARCHAR(64),
                FOREIGN KEY (zone_id) REFERENCES zones(id)
            );""")
def create_zones_table():
    with db.get_cursor() as cursor:
        cursor.execute(f"postgresql://admin:lVZqlZ3q1ldXW3BeNcZSBCTS20E2xr2U@dpg-dc3qec59el5s739au87g-a/circlesqldata;")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE
        );""")
def create_price_table():
    with db.get_cursor() as cursor:
        cursor.execute(f"postgresql://admin:lVZqlZ3q1ldXW3BeNcZSBCTS20E2xr2U@dpg-dc3qec59el5s739au87g-a/circlesqldata;")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_prices (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            item_id INT,
            price DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (item_id) REFERENCES inventory_items(id)
        );""")

"""
here
"""
def verify_supply(order_id):
            with db.get_cursor() as cur:
                cur.execute("""
                    SELECT o.*, i.*
                    FROM orders o
                    LEFT JOIN inventory_items i ON o.id = i.id
                    WHERE o.id = %s
                """, (order_id,))
                return cur.fetchall()
            
"""SELECT FirstName, LastName
    FROM users
    WHERE id IN 
        (SELECT user_id 
        FROM orders 
        WHERE order_date > CURRENT_DATE - INTERVAL '30 days' AND InvoiceNo IN
            (SELECT InvoiceNo 
            FROM stock_orders 
            WHERE PartNo IN
                (SELECT PartNo 
                FROM stock_orders 
                WHERE status = 'Completed')));
"""
def create_invoice_table():
    with db.get_cursor() as cursor:
        cursor.execute(f"postgresql://admin:lVZqlZ3q1ldXW3BeNcZSBCTS20E2xr2U@dpg-dc3qec59el5s739au87g-a/circlesqldata;")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            invoice_number VARCHAR(255) NOT NULL UNIQUE,
            date DATE NOT NULL,
            total DECIMAL(10, 2) NOT NULL
        );""")
def create_parts_table():
    with db.get_cursor() as cursor:
        cursor.execute(f"postgresql://admin:lVZqlZ3q1ldXW3BeNcZSBCTS20E2xr2U@dpg-dc3qec59el5s739au87g-a/circlesqldata;")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            part_number VARCHAR(255) NOT NULL UNIQUE,
            description VARCHAR(255),
            price DECIMAL(10, 2) NOT NULL
        );""")
def create_invoice_line_table():
    with db.get_cursor() as cursor:
        cursor.execute(f"postgresql://admin:lVZqlZ3q1ldXW3BeNcZSBCTS20E2xr2U@dpg-dc3qec59el5s739au87g-a/circlesqldata;")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_line (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            invoice_id INT,
            part_id INT,
            quantity INT NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (part_id) REFERENCES parts(id)
        );""")
    
def get_item_by_id(item_id):
    query = """ SELECT id, sku, name, count, zone FROM inventory_items WHERE id = %s"""
    with db.get_cursor() as cursor:
        cursor.execute(query, (item_id,))
        row = cursor.fetchone()
    zones = {}
    for row in rows:
        zone = row["zone"].lower()
        if zone not in zones:
            zones[zone] =[]
        zones[zone].append({
            "id": row ["id"],
            "sku": row ["sku"],
            "name": row ["name"],
            "count": row ["count"],
            "zone": row ["zone"]
        })
    return zones
# ---------- Zones / inventory ----------
def get_zone_id(zone_name: str) -> int:
    with db.get_cursor() as cur:
        cur.execute("""
        SELECT id FROM 
        zones WHERE name=%s""", (zone_name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute("""
                    INSERT INTO zones (name) 
                    VALUES (%s)
                    RETURNING id
                    """, (zone_name,))
        zone_id = cur.fetchone()["id"]
        return zone_id
    
""" This join function groups the data so that it is easier to access the data from the database and 
display it on the frontend. It also allows for more complex queries to be performed on the data, 
such as filtering by zone or category."""
def sql_join():
    sql_join_tables = """
        SELECT id, sku, name, count, name AS zone
        FROM inventory_items
        JOIN zones ON zone_id = id
        ORDER BY name, name
        """
    with db.get_cursor() as cur:
        cur.execute(sql_join_tables)
        rows = cur.fetchall()
    inventory = {}
    for r in rows:
        z = r["zone"]
        inventory.setdefault(z,[]).append(r)
    return inventory
def get_inventory_by_zone():
        sql_group_data = """
            SELECT id, sku, name, count, zone_id, name AS zone, price AS price
            FROM inventory_items
            JOIN zones ON zone_id = id
            LEFT JOIN item_prices ON id = item_id
            ORDER BY name, name
            """
        with db.get_cursor() as cur:
            cur.execute(sql_group_data)
            rows = cur.fetchall()
        inventory = {}
        for r in rows:
            z = r["zone"].lower()
            inventory.setdefault(z,[]).append(r)
        return inventory
def get_orders():
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM orders")
        return cursor.fetchall()
def get_inventory_prices():
        sql_group_data = """
            SELECT id, sku, name, count, zone_id, name AS zone, price AS price
            FROM inventory_items
            JOIN zones ON zone_id = id
            JOIN item_prices ON id = item_id
            ORDER BY price, sku
            """
        with db.get_cursor() as cur:
            cur.execute(sql_group_data)
            rows = cur.fetchall()
        price = {}
        for r in rows:
            z = r["zone"].lower()
            price.setdefault(z,[]).append(r)
        return price
"""
here
"""
def get_invoice_by_order():
        sql_group_data = """
            SELECT 
                id AS order_id,
                item,
                account,
                sku AS sku,
                name AS item_name,
                price
            FROM orders
            JOIN inventory_items ON item = name
            LEFT JOIN item_prices ON sku = item_id
            ORDER BY id DESC
            """
        with db.get_cursor() as cur:
            cur.execute(sql_group_data)
            rows = cur.fetchall()
        # invoice = {}
        # for r in rows:
        #     invoice.setdefault(default,[]).append(r)
        return rows
def get_orders_by_user():
    sql_group_data = """
            SELECT
                id AS order_id,
                account
            FROM orders
            JOIN users ON account = username
            ORDER BY id DESC
            """
    with db.get_cursor() as cur:
        cur.execute(sql_group_data)
        rows = cur.fetchall()
    orders = {}
    for r in rows:
        z = r["zone"].lower()
        orders.setdefault(z,[]).append(r)
    return orders
        
def get_recent_stock_orders():
    sql_retrieve_stocks = """
            SELECT symbol, strat_name AS strategy, profit, created_at
            FROM stock_orders
            JOIN strategies ON strategy = strat_id
            ORDER BY symbol DESC
        """
    with db.get_cursor() as cur:
        cur.execute(sql_retrieve_stocks)
        rows = cur.fetchall()
    return rows
def get_all_inventory():
    with db.get_cursor() as cur:
        cur.execute("SELECT * FROM inventory_items")
        return cur.fetchall()
def join_planner():
    query = """
        SELECT account, item, quantity, zone
        FROM orders
        JOIN inventory_items ON item = name
        WHERE count >= quantity
    """
    with db.get_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()
def add_or_increment_item(sku, zone, category, value_level, item_name):
    zone_id = get_zone_id(zone)
    with db.get_cursor() as cur:
        cur.execute("""
            SELECT id, count FROM inventory_items
            WHERE zone_id=%s AND LOWER(name)=LOWER(%s)
        """, (zone_id, item_name))
        row = cur.fetchone()
        if row:
            new_count = row["count"] + 1
            cur.execute("UPDATE inventory_items SET count=%s WHERE id=%s",
                        (new_count, row["id"]))
            return row["id"], new_count, False
        if category is None:
            sku_part_1 = 1100
        elif category == "consumable":
            sku_part_1 = 2200
        elif category == "nonconsumable":
            sku_part_1 = 3300
        else:
            sku_part_1 = 4400
        if value_level is None:
            sku_part_2 = 1001
        elif value_level == "a":
            sku_part_2 = 2002
        elif value_level == "b":
            sku_part_2 = 3003
        elif value_level == "c":
            sku_part_2 = 4004
        else:
            sku_part_2 = 5005
        
        sku = f"{(sku_part_1)}{(sku_part_2)}"
        cur.execute("""
            INSERT INTO inventory_items (name, count, zone_id, category, value_level, sku)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (item_name, 1, zone_id, category, value_level, sku))
        zone_id = cur.fetchone()["id"]
        return zone_id, 1, True
def update_user_invoice(username:str, invoice_number:str):
    with db.get_cursor() as cursor:
        cursor.execute("postgresql://admin:lVZqlZ3q1ldXW3BeNcZSBCTS20E2xr2U@dpg-dc3qec59el5s739au87g-a/circlesqldata;")
        cursor.execute("""
            UPDATE invoices 
                SET invoice_number = %s
                WHERE invoice_number = (
                    SELECT invoice_id FROM users
                    WHERE username = %s
                )
        """, (invoice_number, username))
def delete_user_invoice(username:str, invoice_id:str):
    with db.get_cursor() as cursor:
        cursor.execute("postgresql://admin:lVZqlZ3q1ldXW3BeNcZSBCTS20E2xr2U@dpg-dc3qec59el5s739au87g-a/circlesqldata;")
        cursor.execute("""
            DELETE FROM invoices
                WHERE invoice_id = (
                    SELECT invoice_id 
                    FROM users
                    WHERE username = %s
                )   
        """, (username, invoice_id))
def input_item_price(item_id, price):
    with db.get_cursor() as cur:
        cur.execute("""
            INSERT INTO item_prices (item_id, price)
            VALUES (%s, %s)
            RETURNING id
        """, (item_id, price))
        zone_id = cur.fetchone()["id"]
        return zone_id

def update_inventory_item(item_id, new_name):
    with db.get_cursor() as cur:
        cur.execute("UPDATE inventory_items SET name=%s WHERE id=%s",
                    (new_name, item_id))
        return cur.rowcount > 0

def delete_inventory_item(item_id):
    with db.get_cursor() as cur:
        cur.execute("DELETE FROM inventory_items WHERE id=%s", (item_id,))
        return cur.rowcount > 0
def search_contacts(query: str):
    sql = """
    SELECT id, CONCAT(first, ' ', last) AS name, email
    FROM contactsTable
    WHERE Phone_Number LIKE %s OR CONCAT(first, ' ', last) LIKE %s
    """
    with db.get_cursor() as cur:
        cur.execute(sql, (f"%{query}%", f"%{query}%"))
        return cur.fetchall()

def create_order(account, item, quantity):
    with db.get_cursor() as cursor:
        sql = """INSERT INTO orders (account, item, quantity) 
                  VALUES (%s, %s, %s)
                  RETURNING id"""
        cursor.execute(sql, (account, item, quantity))
        zone_id = cur.fetchone()["id"]
        db.connection.commit()
        return zone_id
def get_orders():
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM orders")
        return cursor.fetchall()
def update_order(order_id, new_quantity):
    with db.get_cursor() as cursor:
        sql = "UPDATE orders SET quantity = %s WHERE id = %s"
        cursor.execute(sql, (new_quantity, order_id))
        return cursor.fetchall()
def delete_order(order_id):
    with db.get_cursor() as cursor:
        sql = "DELETE FROM orders WHERE id = %s"
        cursor.execute(sql, (order_id,))
        db.connection.commit()
        return cursor.rowcount
    
@backend_site.route("/verify_supply", methods=["GET", "POST"])
def verification():
    if request.method =='POST':
        action = request.form.get('action')
        order_id = request.form.get('order_id')
        try:
            if action == 'check':
                valid = verify_supply(order_id)
                if valid:
                    flash(f"Order {order_id} is valid and can be fulfilled.")
                else:
                    flash(f"Order {order_id} cannot be fulfilled due to insufficient inventory.")
            elif action == 'update':
                username = request.form.get('username')
                invoice_number = request.form.get('invoice_number')
                update_user_invoice(username=username, invoice_number=invoice_number)
                flash(f"Invoice number for user {username} updated to {invoice_number}.")

        except Exception as e:
                    logger.error(e)
                    flash("Error", "error")
    
    invoice = get_invoice_by_order()
    user_orders = get_orders_by_user()
    order_items = get_inventory_by_zone()
    inventory_items = get_all_inventory()
    
    return render_template("supply_template.html", invoice=invoice, user_orders=user_orders, orders_items=order_items, inventory_items=inventory_items)


# to be continued; this is a work in progress
@backend_site.route('/place_order', methods=['GET', 'POST'])
def place_order():
    if request.method == 'POST':
        action = request.form.get('action')
        account = request.form.get('account')
        item = request.form.get('item')
        quantity = request.form.get('quantity')
        try:
            if action == 'create':
                create_order(account, item, quantity)
                flash("order added", "success")
            elif action == 'update':
                order_id = request.form.get('order_id')
                update_order(order_id, quantity)
                flash("updated", "success")
        except Exception as e:
            logger.error(e)
            flash("Error creating order.", "error")
    orders = get_invoice_by_order()

    return render_template("order_placement_template.html", orders=orders)
from flask import make_response

@backend_site.after_request
def add_custom_header(response):
    response.headers["X-Inventory-App-backend"] = "test-lab"
    return response

@backend_site.route('/scanner', methods=['GET', 'POST'])
def scanner():
    create_zones_table()
    create_inventory_items_table()
    create_price_table()
    create_invoice_table()
    create_parts_table()
    create_invoice_line_table()
    if request.method =='POST':
        action = request.form.get('action')
        zone = request.form.get('zone')
        item_name = request.form.get('item','').strip()
        item_id = request.form.get('item_id')
        category = request.form.get('category')
        value = request.form.get('value')
        price =request.form.get('price')
        try:
            if action == 'add':
                add_or_increment_item(sku=None, zone=zone, category=category, value_level=value, item_name=item_name)
                if price: 
                    input_item_price(item_id, price)
                flash('added')
            elif action == 'edit':
                update_inventory_item(item_id, item_name)
                flash('edited')
            elif action == 'delete':
                delete_inventory_item(item_id)
                flash('deleted')
        except Exception as e:
            logger.error(e)
            flash("Error", "error")        
        return redirect(url_for('backend_site.scanner'))
    
    inventory = get_inventory_by_zone()
    price = get_inventory_prices()
    summary = build_summary(inventory)
    return render_template('scanner_template.html', 
                            inventory=inventory,
                            price=price,
                            summary=summary)

"""     As an inventory system this api utility finds and sorts product id  """
@backend_site.route('/api/zone/<zone_name>', methods=['GET'])
def api_get_zone(zone_name):
    db = DatabaseManager()
    inventory = get_inventory_by_zone()
    zone_name = zone_name.lower()
    if zone_name not in inventory:
        return{"error"}, 404
    zone_items = inventory[zone_name]

    return {"zone": zone_name,
            "count": len(zone_items),
            "items": zone_items}
@backend_site.route('/api/zone/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = get_item_by_id(item_id)
    if item is None:
        return {"error"}, 404
    return item
@backend_site.route('/api', methods=['GET'])
def api():
    inventory = get_inventory_by_zone()
    return render_template('api_template.html', inventory=inventory)

"""     Todo; create a page that is able to calculate assorted financial information    """
@backend_site.route('/zone', methods=['GET', 'POST'])
def zone():
    # Handle POST actions
    if request.method == 'POST':
        action = request.form.get('action')
        category = request.form.get('category', '')
        abc_value = request.form.get('value', '').strip()
        zone_name = request.form.get('zone', '').strip()    #   This accesses zone locations
        item = request.form.get('item', '').strip()
        # count_var += 1        
#   add a sku value to items as well as count available in inventory
#   sku will make it easier to filter in db
#   each item in json should be saved with a sku, 
# (reiterates the id in human readable format) item name, location, and count
#   Change the zone variables to be specific to database
        if action == 'add' and zone_name in ['freezer', 'fridge', 'dry', 'other'] and item:
            try:
                item_id, count, created = add_or_increment_item(
                    zone_name, item, category=category, value_level=abc_value)
                if created:
                    flash(f"created {item}")
            except Exception as e:
                logger.error("failed")
        elif action == 'edit':
            item_id = request.form.get('item_id')
            try:
                if update_inventory_item(item_id, item):
                    flash("updated")
            except Exception as e:
                logger.error("failed")
        
        elif action == 'delete':
            item_id = request.form.get('item_id')
            try:
                if delete_inventory_item(item_id):
                    flash('deleted')
            except Exception as e:
                logger.error('failed')
            
    inventory = get_inventory_by_zone()    
    # Build HTML - FIXED STRUCTURE
    zones_html = ""  # Initialize!
    for zone_name, items in inventory.items():
        # FIXED: items_html is separate variable
        items_html = "".join(
            f"<tr><td>{item('name')} <strong style='color:#4caf50'>(x{item('count')})</strong> "
            f"<br><b><small>SKU: {item('sku', 'N/A')}</small></b></td>"
            f"<td><mark><input value=\"{item('name')}\" style=\"width:120px;padding:4px;\" "
            f"onchange=\"updateItem('{zone_name}', '{item('id')}', this.value)\"></mark></td>"
            f"<td><button onclick=\"deleteItem('{zone_name}', '{item('id')}')\" "
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
"""     connects with the api to retreive data from the database    """
@backend_site.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = []
    db = DatabaseManager()
    if query:
        try:
            results = search_contacts(query)
        except Exception as e:
            logger.error("failed")
    return render_template('search.html', results=results, query=query)
#   use this as a tool that can adjust for periods that have surplus or deficit 

"""  Add in average calculation this might be similar to the forecasting   """
@backend_site.route('/time_frame', methods=['GET', 'POST'])
def time_frame():
    message = ""
    db = DatabaseManager()
    if request.method == 'POST':
        try:
            prod = request.form.get('prod', '').strip()
            stock_order = int(request.form.get('stock_order', 0))
            variance = int(request.form.get('variance', 0))
            season = request.form.get('season', 'winter')
            _, order_qty = add_stock_order(prod, stock_order, variance, season)
        except ValueError:
            flash("enter valid numbers")
        except Exception as e:
            logger.error("failed")
    recent_orders = get_recent_stock_orders(limit=5)
    print("Recent orders:", recent_orders)  # Debugging output
    orders_html = "".join(
        f"<div style='padding: 8px; border-bottom: 1px solid #eee;'>{d['prod']}: "
        f"<strong>{d['order_qty']}</strong> ({d['season']}) - {d.get('timestamp', 'N/A')}</div>"
        for d in reversed(recent_orders)
    ) or "<p>No orders yet</p>"
    return render_template('time_frame_template.html', orders_html=orders_html)
