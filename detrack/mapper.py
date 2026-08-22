# Convert Shopify timeslot into Detrack label
def map_timeslot_to_detrack(order):
    if order.delivery_type == "Pickup":
        return "PICK UP"

    timeslot_mapping = {
        "9:00 AM - 2:00 PM": "AM",
        "1:00 PM - 6:00 PM": "PM",
        "5:00 PM - 10:00 PM": "NIGHT",
    }

    return timeslot_mapping.get(order.delivery_slot)