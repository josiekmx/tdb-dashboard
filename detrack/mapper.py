# Convert Shopify timeslot into the label printed on Detrack tags
def map_timeslot_to_detrack(order):
    if order.delivery_type == "Pickup":
        if order.delivery_slot:
            return f"PICK UP {order.delivery_slot}"
        return "PICK UP"

    timeslot_mapping = {
        "9:00 AM - 2:00 PM": "AM",
        "1:00 PM - 6:00 PM": "PM",
        "5:00 PM - 10:00 PM": "NIGHT",
    }

    return timeslot_mapping.get(order.delivery_slot)