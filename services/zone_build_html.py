def build_zone_tables(inventory):
    zones_html = ""
    for zone_name, items in inventory.items():
        rows = "".join(
            f"<tr><td>{item['name']}</td><td>{item['sku']}</td><td>{item['count']}</td>"
            f"<td><button onclick=\"editItem('{zone_name}', '{item['id']}', this.value)\">Edit</button></td>"
            f"<td><button onclick=\"deleteItem('{zone_name}', '{item['id']}')\">Delete</button></td></tr>"
            for item in items
        ) or "<tr><td colspan='4'>No items in this zone.</td></tr>"

        zones_html += f"""
        <div>
            <h2>{zone_name.title()}</h2>
            <table><tbody>{rows}</tbody></table>
        </div>
        """

    return zones_html