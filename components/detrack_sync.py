import pandas as pd
import streamlit as st

from shopify_client import get_orders
from detrack.order_builder import build_delivery_orders
from detrack.sku_mapping import get_sku_tag_mapping
from detrack.tag_calculator import calculate_tags
from detrack.validator import validate_order
from detrack.mapper import map_timeslot_to_detrack, map_orders_to_detrack


# Build and validate upcoming unfulfilled Shopify orders for Detrack
def prepare_detrack_orders():
    orders = get_orders()

    # Only keep orders that are not fully fulfilled
    unfulfilled_orders = [
        order
        for order in orders
        if order.get("fulfillment_status") != "fulfilled"
    ]

    delivery_orders = build_delivery_orders(unfulfilled_orders)
    sku_mapping = get_sku_tag_mapping()

    # Calculate tag quantity and validate each order
    for order in delivery_orders:
        total_tags, missing_skus = calculate_tags(
            order,
            sku_mapping
        )

        order.number_of_tags = total_tags
        validate_order(order, missing_skus)

    # Only keep delivery / pickup dates from today onwards
    today = pd.Timestamp.now(tz="Asia/Singapore").date()

    delivery_orders = [
        order
        for order in delivery_orders
        if order.delivery_date
        and pd.to_datetime(order.delivery_date).date() >= today
    ]

    return delivery_orders


# Display Detrack orders by selected delivery / pickup date
def display_detrack_sync():
    st.subheader("Detrack Sync")

    delivery_orders = prepare_detrack_orders()

    # Get available upcoming order dates
    available_dates = sorted({
        order.delivery_date
        for order in delivery_orders
        if order.delivery_date
    })

    if not available_dates:
        st.info("No upcoming unfulfilled orders found.")
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

    # Preview only READY and WARNING orders that are eligible for Detrack upload
    st.subheader("Detrack Upload Preview")

    eligible_orders = [
        order
        for order in date_orders
        if order.validation_status in ["READY", "WARNING"]
    ]

    detrack_rows = map_orders_to_detrack(eligible_orders)
    detrack_df = pd.DataFrame(detrack_rows)

    st.dataframe(
        detrack_df,
        use_container_width=True,
        hide_index=True
    )
