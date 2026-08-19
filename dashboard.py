import streamlit as st
from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables
from shopify_client import get_orders

# TEMPORARY: inspect remaining Shopify fields needed for Detrack
orders = get_orders()
test_order = orders[0]

# Display shipping address field names
st.write("SHIPPING ADDRESS FIELDS")
st.write(list((test_order.get("shipping_address") or {}).keys()))

# Display order-level note attribute names
st.write("NOTE ATTRIBUTE NAMES")
for attr in test_order.get("note_attributes", []):
    st.write(attr.get("name"))

# Display line-item property names
st.write("LINE ITEM PROPERTIES")
for item in test_order.get("line_items", []):
    for prop in item.get("properties", []):
        st.write(prop.get("name"))

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
