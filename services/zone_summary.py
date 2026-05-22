def build_zone_summary(inventory):
    return "".join(
        f"<div><strong>{zone.title()}</strong> "
        f"{', '.join(item['name'] for item in items) or 'Empty'}</div>"
        for zone, items in inventory.items()
    )