# Build one Detrack API payload from a validated TDB order
def build_detrack_payload(order, timeslot_label):
    items = []

    # Build all Shopify line items under one Detrack job
    for item in order.line_items:
        items.append({
            "sku": item.sku,
            "description": timeslot_label,
            "quantity": item.quantity,
        })

    payload = {
        "do_number": order.order_number,
        "date": order.delivery_date,

        # Recipient / delivery details
        "address": order.address or "",
        "postal_code": order.postal_code or "",
        "deliver_to_collect_from": order.recipient_name or "",
        "phone_number": order.recipient_phone or "",

        # Sender details
        "sender_name": order.sender_name or "",
        "sender_email": order.sender_email or "",
        "sender_phone_number": order.sender_phone or "",

        # Optional order note
        "instructions": order.additional_request or "",

        # Detrack settings
        "group": "The Daily Blooms",
        "number_of_shipping_labels": order.number_of_tags,

        # Shopify products
        "items": items,
    }

    return payload