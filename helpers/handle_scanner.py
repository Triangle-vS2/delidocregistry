from utilities.interact_json import get_inventory_with_ids, save_json_data, update_inventory_item

def handle_scanner_post(form_data, filename):
    action = form.get('action')
    zone = form.get('zone')
    item = form.get('item')

    delivery = get_inventory_with_ids(filename)

    if action == 'add':
        add_item(delivery, zone, form)
    elif action == 'edit':
        update_inventory_item(filename, zone, form.get('item_id'), item)
    elif action == 'delete':
        delete_delivery_item(delivery_filename, zone, form.get('item_id'))
    
    save_json_data(delivery_filename, delivery)