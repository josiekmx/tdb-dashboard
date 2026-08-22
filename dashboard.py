import streamlit as st
from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables
from shopify_client import get_orders

from shopify_client import get_orders
from detrack.order_builder import build_delivery_orders
from detrack.sku_mapping import get_sku_tag_mapping
from detrack.tag_calculator import calculate_tags
from detrack.validator import validate_order

#----------------------- TESTING CODE -----------------------
# TEMPORARY: build one Shopify order and test tag calculation + validation
orders = get_orders()
delivery_orders = build_delivery_orders(orders)
sku_mapping = get_sku_tag_mapping()

test_order = delivery_orders[0]

# TEMPORARY: force a missing SKU mapping to test validation
test_order.line_items[0].sku = ""
total_tags, missing_skus = calculate_tags(
    test_order,
    sku_mapping
)


test_order.number_of_tags = total_tags
test_order = validate_order(test_order, missing_skus)

# Apply tag count and validate the order
test_order.number_of_tags = total_tags
test_order = validate_order(test_order, missing_skus)

st.write("ORDER", test_order.order_number)
st.write("TAGS REQUIRED", test_order.number_of_tags)
st.write("STATUS", test_order.validation_status)
st.write("VALIDATION", test_order.validation_messages)

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

# dashboard header
st.header("The Daily Blooms Dashboard")

# enables refresh
# upon refresh, the date and timeslots will return to 
# default state of the earliest date and all timeslots respectively. 
if st.button("Refresh"):
    # Reset filters
    st.session_state.selected_date = None
    st.session_state.selected_slots = []
    st.rerun()

# insert empty space to optimise ui
st.markdown("<br>", unsafe_allow_html=True)

# order details table
filtered_table_data = display_order_details_table()

# summary tables 
display_order_summary_tables(filtered_table_data)
