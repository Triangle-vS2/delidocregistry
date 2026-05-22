from flask import Blueprint, render_template, request, redirect, url_for, flash

from helpers.inventory_loader import get_inventory, save_json_data

from services.zone_add import handle_add
from services.zone_edit import handle_edit
from services.zone_delete import handle_delete
from services.zone_build_html import build_zone_tables
from services.zone_summary import build_zone_summary

zone_bp = Blueprint('zone', __name__)

@zone_bp.route('/zone', methods=['GET', 'POST'])
def zone():
    filename = 'data/data.json'

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            handle_add(request.form)
        elif action == 'edit':
            handle_edit(request.form)
        elif action == 'delete':
            handle_delete(request.form)
        else:
            flash('Invalid action', 'error')
    inventory = get_inventory()
    zones_html = build_zone_tables(inventory)
    zones_display = build_zone_summary(inventory)    
    return render_template(
        'zone_template.html',
        zones_html=zones_html,
        zones_display=zones_display,
        inventory=inventory
    )