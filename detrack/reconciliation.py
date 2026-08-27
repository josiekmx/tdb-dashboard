# ---------------------------------------------------------
# DETRACK DELIVERY RECONCILIATION
# ---------------------------------------------------------

# Delivery cycles used for Detrack reconciliation.
# Pickup orders are intentionally excluded.
DELIVERY_CYCLES = {
    "AM": {
        "label": "AM · 9–2",
        "timeslot": "9:00 AM - 2:00 PM",
        "cutoff": "08:30",
    },
    "PM": {
        "label": "PM · 1–6",
        "timeslot": "1:00 PM - 6:00 PM",
        "cutoff": "12:30",
    },
    "NIGHT": {
        "label": "NIGHT · 5–10",
        "timeslot": "5:00 PM - 10:00 PM",
        "cutoff": "16:30",
    },
}


# ---------------------------------------------------------
# FILTER DELIVERY ORDERS BY CYCLE
# ---------------------------------------------------------

def get_cycle_delivery_orders(
    date_orders,
    timeslot,
):
    """
    Return Delivery orders belonging to one delivery cycle.

    Pickup orders are intentionally excluded.
    """

    return [
        order
        for order in date_orders
        if order.delivery_type == "Delivery"
        and order.delivery_slot == timeslot
    ]


# ---------------------------------------------------------
# RECONCILE ONE DELIVERY CYCLE
# ---------------------------------------------------------

def reconcile_delivery_cycle(
    date_orders,
    existing_detrack_orders,
    timeslot,
):
    """
    Compare Shopify Delivery orders against order numbers
    currently found in Detrack for one delivery cycle.
    """

    cycle_orders = get_cycle_delivery_orders(
        date_orders,
        timeslot,
    )

    shopify_count = len(cycle_orders)

    orders_in_detrack = [
        order
        for order in cycle_orders
        if order.order_number
        in existing_detrack_orders
    ]

    missing_orders = [
        order
        for order in cycle_orders
        if order.order_number
        not in existing_detrack_orders
    ]

    return {
        "shopify_count": shopify_count,
        "detrack_count": len(
            orders_in_detrack
        ),
        "missing_count": len(
            missing_orders
        ),

        # Keep these internally.
        # We will decide when to display them
        # after adding cutoff logic later.
        "missing_order_numbers": [
            order.order_number
            for order in missing_orders
        ],
    }


# ---------------------------------------------------------
# RECONCILE ALL DELIVERY CYCLES
# ---------------------------------------------------------

def reconcile_delivery_cycles(
    date_orders,
    existing_detrack_orders,
):
    """
    Reconcile AM, PM and NIGHT Delivery orders.

    Returns one summary dictionary per delivery cycle.
    """

    results = {}

    for cycle_name, cycle in (
        DELIVERY_CYCLES.items()
    ):
        reconciliation = (
            reconcile_delivery_cycle(
                date_orders,
                existing_detrack_orders,
                cycle["timeslot"],
            )
        )

        results[cycle_name] = {
            "label": cycle["label"],
            "timeslot": cycle["timeslot"],
            "cutoff": cycle["cutoff"],
            **reconciliation,
        }

    return results