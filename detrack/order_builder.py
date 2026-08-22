import re

from detrack.models import DeliveryLineItem, TDBDeliveryOrder


# Get a custom property from a Shopify line item
def get_property(item, property_name):
    for prop in item.get("properties", []):
        if prop.get("name") == property_name:
            return prop.get("value")

    return None


# Find the first matching property across all line items in an order
def get_order_property(order, property_name):
    for item in order.get("line_items", []):
        value = get_property(item, property_name)

        if value:
            return value

    return None


# Extract the current delivery / pickup date from Shopify tags
def get_date_from_tags(tags):
    match = re.search(r"\d{4}-\d{2}-\d{2}", tags or "")

    if match:
        return match.group()

    return None


# Extract the current delivery / pickup timeslot from Shopify tags
# Extract the current delivery / pickup timeslot from Shopify tags
def get_timeslot_from_tags(tags):
    tags = tags or ""

    # Delivery slots
    delivery_slots = [
        "9:00 AM - 2:00 PM",
        "1:00 PM - 6:00 PM",
        "5:00 PM - 10:00 PM",
    ]

    # Pickup slots
    pickup_slots = [
        "9:00 AM - 12:00 PM",
        "12:00 PM - 3:00 PM",
        "3:00 PM - 5:00 PM",
        "5:00 PM - 9:00 PM",
    ]

    # Check pickup slots first
    for timeslot in pickup_slots:
        if timeslot in tags:
            return timeslot

    # Check delivery slots
    for timeslot in delivery_slots:
        if timeslot in tags:
            return timeslot

    return None


# Determine whether the Shopify order is Delivery or Pickup
def get_delivery_type(order):
    tags = order.get("tags", "").lower()

    if "pickup" in tags or "pick up" in tags:
        return "Pickup"

    if "delivery" in tags:
        return "Delivery"

    return get_order_property(order, "Selection")


# Combine Shopify address1 and address2 into one delivery address
def build_address(order):
    shipping = order.get("shipping_address") or {}

    address_parts = [
        shipping.get("address1"),
        shipping.get("address2"),
    ]

    return ", ".join(
        str(part).strip()
        for part in address_parts
        if part and str(part).strip()
    )


# Keep every Shopify line item for SKU tag calculations later
def build_line_items(order):
    line_items = []

    for item in order.get("line_items", []):
        line_items.append(
            DeliveryLineItem(
                # Use a standard fallback for custom products without a SKU
                sku=item.get("sku") or "No SKU - check custom order",
                product=item.get("title") or "",
                quantity=item.get("quantity") or 0,
            )
        )

    return line_items


# Convert one raw Shopify order into our standard TDB delivery structure
def build_delivery_order(order):
    shipping = order.get("shipping_address") or {}

    return TDBDeliveryOrder(
        shopify_id=str(order.get("id", "")),
        order_number=order.get("name", ""),

        delivery_date=get_date_from_tags(order.get("tags")),
        delivery_slot=get_timeslot_from_tags(order.get("tags")),
        delivery_type=get_delivery_type(order),

        recipient_name=shipping.get("name"),
        recipient_phone=shipping.get("phone"),

        address=build_address(order),
        postal_code=shipping.get("zip"),

        additional_request=order.get("note"),
        card_to=get_order_property(order, "To"),
        card_message=get_order_property(order, "Message"),

        line_items=build_line_items(order),
    )


# Convert a list of Shopify orders into TDB delivery orders
def build_delivery_orders(orders):
    return [
        build_delivery_order(order)
        for order in orders
    ]