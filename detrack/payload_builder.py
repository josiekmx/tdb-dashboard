# Build one Detrack API payload from a validated TDB order
def build_detrack_payload(order, timeslot_label):
    items = []

    # Add every Shopify line item to the Detrack job
    for item in order.line_items:
        items.append({
            "sku": item.sku,
            "description": timeslot_label,
            "quantity": item.quantity,
        })

    return {
        "type": "Delivery",
        "do_number": order.order_number,
        "date": order.delivery_date,

        # Delivery / recipient details
        "address": order.address or "",
        "postal_code": order.postal_code or "",
        "deliver_to_collect_from": order.recipient_name or "",
        "phone": order.recipient_phone or "",

        # Operational details
        "instructions": order.additional_request or "",
        "group": "The Daily Blooms",
        "number_of_shipping_labels": order.number_of_tags,

        # Sender / purchaser details
        "sender_name": order.sender_name or "",
        "sender_email": order.sender_email or "",
        "sender_phone": order.sender_phone or "",

        # Shopify products
        "items": items,
    }    