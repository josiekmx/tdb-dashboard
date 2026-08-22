import pandas as pd
import streamlit as st

from shopify_client import get_orders
from detrack.order_builder import build_delivery_orders
from detrack.sku_mapping import get_sku_tag_mapping
from detrack.tag_calculator import calculate_tags
from detrack.validator import validate_order


# Build and validate all Shopify orders for Detrack
def prepare_detrack_orders():
    orders = get_orders()
    delivery_orders = build_delivery_orders(orders)
    sku_mapping = get_sku_tag_mapping()

    for order in delivery_orders:
        total_tags, missing_skus = calculate_tags(order, sku_mapping)

        order.number_of_tags = total_tags
        validate_order(order, missing_skus)

    return delivery_orders


# Display Detrack-ready orders as a preview table
def display_detrack_sync():
    st.subheader("Detrack Sync")

    delivery_orders = prepare_detrack_orders()

    rows = []

    for order in delivery_orders:
        rows.append({
            "Order": order.order_number,
            "Date": order.delivery_date,
            "Type": order.delivery_type,
            "Timeslot": order.delivery_slot,
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