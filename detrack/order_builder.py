#RAW SHOPIFY ORDER
#        ↓
#extract the information we need
#        ↓
#TDBDeliveryOrder

from detrack.models import DeliveryLineItem, TDBDeliveryOrder

# ============================================================
# GET LINE ITEM PROPERTY
# ============================================================
#properties = [
#     {"name": "Delivery Date", "value": "2026-08-20"},
#     {"name": "Recipient Name", "value": "Sarah"},
# ]
## This helper searches those properties for a particular name.
# Example:
# get_property(item, "Delivery Date")
# returns:
# "2026-08-20"
# If the property does not exist, it returns None.

def get_property(item, property_name):
    for prop in item.get("properties", []):
        if prop.get("name") == property_name:
            return prop.get("value")

    return None


# ============================================================
# BUILD DELIVERY LINE ITEMS
# ============================================================
# Converts Shopify's line_items into our simpler
# DeliveryLineItem structure.    
# Unlike the existing order_processor.py, this function keeps
# ALL line items.

def build_line_items(order):

    line_items = []

    for item in order.get("line_items", []):

        line_items.append(
            DeliveryLineItem(
                sku=item.get("sku") or "",
                product=item.get("title") or "",
                quantity=item.get("quantity") or 0,
            )
        )

    return line_items

