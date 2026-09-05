import streamlit as st
from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables
from shopify_client import get_orders

from detrack.order_builder import build_delivery_orders
from detrack.sku_mapping import get_sku_tag_mapping
from detrack.tag_calculator import calculate_tags
from detrack.validator import validate_order

from components.detrack_sync import display_detrack_sync

#----------------------- TESTING CODE -----------------------

def display_polaroid_test():
    st.subheader("Polaroid Upload Test")

    test_order = st.text_input(
        "Enter Shopify order number",
        placeholder="#TDBXXXXX"
    )

    if not test_order:
        st.info("Enter an order number containing a Polaroid upload.")
        return

    orders = get_orders()

    matched_order = None

    for order in orders:
        if order.get("name") == test_order:
            matched_order = order
            break

    if not matched_order:
        st.error(f"Order {test_order} not found.")
        return

    st.success(f"Found {matched_order.get('name')}")

    for item in matched_order.get("line_items", []):
        st.divider()

        st.write("**Item:**", item.get("title"))
        st.write("**SKU:**", item.get("sku"))
        st.write("**Line Item ID:**", item.get("id"))

        st.write("**Properties:**")

        properties = item.get("properties", [])

        if not properties:
            st.write("No line item properties found.")

        for prop in properties:
            st.write(prop)


#----------------------- original code below -----------------------

# displays login page to authenticate users
if not check_password():
    st.stop()

# set windows tab
st.set_page_config(
    page_title="The Daily Blooms Dashboard",
    page_icon="assets/flower_logo.png",
    layout="wide"
)

# Dashboard header with refresh button on the right
header_col, refresh_col = st.columns([8, 1])

with header_col:
    st.header("The Daily Blooms Dashboard")

with refresh_col:
    if st.button("Refresh", use_container_width=True):
        st.rerun()

# Main dashboard sections
orders_tab, detrack_tab, polaroid_test_tab = st.tabs([
    "Orders",
    "Detrack Sync",
    "Polaroid Test"
])

with orders_tab:
    # order details table
    filtered_table_data = display_order_details_table()

    # summary tables
    display_order_summary_tables(filtered_table_data)

with detrack_tab:
    display_detrack_sync()

with polaroid_test_tab:
    display_polaroid_test()

# enables refresh
# upon refresh, the date and timeslots will return to
# default state of the earliest date and all timeslots respectively.
#if st.button("Refresh"):
    # Reset filters
    #st.session_state.selected_date = None
    #st.session_state.selected_slots = []
    #st.rerun()

# insert empty space to optimise ui
st.markdown("<br>", unsafe_allow_html=True)