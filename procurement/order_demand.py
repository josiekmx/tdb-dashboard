
from datetime import date

from detrack.order_builder import get_date_from_tags


def build_order_demand(orders, start_date, end_date):
    """
    Convert Shopify orders into outstanding SKU demand.

    This function only processes the orders supplied to it.
    It does not fetch or modify Shopify orders.
    """

    start_date = date.fromisoformat(str(start_date))
    end_date = date.fromisoformat(str(end_date))

    if start_date > end_date:
        raise ValueError("Start date must be before end date.")

    demand_rows = []
    warnings = []
    matched_orders = set()

    for order in orders:
        order_id = order.get("id")
        order_name = order.get("name", str(order_id))
        tags = order.get("tags", "")

        if order.get("cancelled_at"):
            continue

        if order.get("fulfillment_status") == "fulfilled":
            continue

        # Reuse existing Detrack parser
        delivery_date_text = get_date_from_tags(tags)

        if not delivery_date_text:
            warnings.append({
                "Order": order_name,
                "Issue": "Missing delivery date in tags",
            })
            continue

        try:
            delivery_date = date.fromisoformat(
                delivery_date_text
            )
        except ValueError:
            warnings.append({
                "Order": order_name,
                "Issue": "Invalid delivery date",
            })
            continue

        if not start_date <= delivery_date <= end_date:
            continue

        matched_orders.add(order_id)

        for item in order.get("line_items", []):
            sku = str(item.get("sku") or "").strip()

            ordered = int(item.get("quantity") or 0)
            fulfilled = int(
                item.get("fulfillable_quantity")
                if item.get("fulfillable_quantity") is not None
                else 0
            )

            # Shopify fulfillable_quantity represents
            # quantity still eligible for fulfillment.
            outstanding = fulfilled

            if outstanding <= 0:
                continue

            if not sku:
                warnings.append({
                    "Order": order_name,
                    "Issue": "Line item has no SKU",
                })
                continue

            demand_rows.append({
                "Order": order_name,
                "Delivery Date": str(delivery_date),
                "SKU": sku,
                "Ordered Qty": ordered,
                "Outstanding Qty": outstanding,
            })

    return {
        "orders_count": len(matched_orders),
        "demand_rows": demand_rows,
        "warnings": warnings,
        "total_outstanding": sum(
            row["Outstanding Qty"]
            for row in demand_rows
        ),
    }
