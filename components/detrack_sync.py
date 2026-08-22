import pandas as pd
import streamlit as st

from shopify_client import get_orders
from detrack.order_builder import build_delivery_orders
from detrack.sku_mapping import get_sku_tag_mapping
from detrack.tag_calculator import calculate_tags
from detrack.validator import validate_order
from detrack.mapper import map_timeslot_to_detrack


# Build and validate all Shopify orders for Detrack
def prepare_detrack_orders():
    orders = get_orders()
    delivery_orders = build_delivery_orders(orders)
    sku_mapping = get_sku_tag_mapping()

    for order in delivery_orders:
        total_tags, missing_skus = calculate_tags(
            order,
            sku_mapping
        )

        order.number_of_tags = total_tags
        validate_order(order, missing_skus)

    return delivery_orders


# Display Detrack orders by selected delivery / pickup date
def display_detrack_sync():
    st.subheader("Detrack Sync")

    delivery_orders = prepare_detrack_orders()

    # Get available order dates
    available_dates = sorted({
        order.delivery_date
        for order in delivery_orders
        if order.delivery_date
    })

    if not available_dates:
        st.info("No upcoming orders found.")
        return

    # Select which date to prepare for Detrack
    selected_date = st.selectbox(
        "Delivery / Pickup Date",
        available_dates
    )

    # Keep only orders for selected date
    date_orders = [
        order
        for order in delivery_orders
        if order.delivery_date == selected_date
    ]

    rows = []

    # Build Detrack preview
    for order in date_orders:
        rows.append({
            "Order": order.order_number,
            "Type": order.delivery_type,
            "Timeslot": map_timeslot_to_detrack(order),
            "Recipient": order.recipient_name,
            "Tags": order.number_of_tags,
            "Status": order.validation_status,
            "Issues": ", ".join(order.validation_messages),
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )