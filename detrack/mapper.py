# Convert Shopify timeslot into the label printed on Detrack tags
def map_timeslot_to_detrack(order):
    # Pickup keeps its actual collection window
    if order.delivery_type == "Pickup":
        if order.delivery_slot:
            return f"PICK UP {order.delivery_slot}"
        return "PICK UP"

    # Delivery uses simplified labels
    timeslot_mapping = {
        "9:00 AM - 2:00 PM": "AM",
        "1:00 PM - 6:00 PM": "PM",
        "5:00 PM - 10:00 PM": "NIGHT",
    }

    return timeslot_mapping.get(order.delivery_slot)


# Convert one TDB order into the rows required by Detrack
def map_order_to_detrack(order):
    rows = []

    timeslot_label = map_timeslot_to_detrack(order)

    for index, item in enumerate(order.line_items):
        rows.append({
            "Order ID": order.order_number,

            # Keep Shopify tag date as-is for now; format for Detrack later
            "Delivery Date": order.delivery_date,

            # Column C
            "Delivery Timeslot": timeslot_label,

            # Unused Detrack fields
            "Job type": None,
            "Job Sequence": None,

            # Column F intentionally ignored
            "Delivery Address F": None,

            "Company Name": None,

            # Column H - actual address used
            "Delivery Address": order.address,

            "Postal Code": order.postal_code,
            "Recipient's Name": order.recipient_name,
            "Recipient Number": order.recipient_phone,

            # Billing phone
            "Sender's Contact": order.sender_phone,

            # Optional Shopify order note
            "Notes": order.additional_request,

            "Assign to": None,

            # Purchaser / sender details
            "Sender Email": order.sender_email,
            "Sender Name": order.sender_name,

            # Fixed group used in Detrack
            "Group": "The Daily Blooms",

            # Detrack reads tag quantity from first SKU line only
            "No. of tags": (
                order.number_of_tags
                if index == 0
                else None
            ),

            "Run No.": None,
            "Service Time": None,
            "Recipient name": None,

            # One Detrack item row per Shopify line item
            "SKU": item.sku,

            # Workaround used for physical tag printing
            "Item Description": timeslot_label,

            "Quantity": item.quantity,
        })

    return rows


# Convert multiple TDB orders into one flat list of Detrack rows
def map_orders_to_detrack(orders):
    rows = []

    for order in orders:
        rows.extend(map_order_to_detrack(order))

    return rows