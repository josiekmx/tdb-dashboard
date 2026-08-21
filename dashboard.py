import streamlit as st
from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables
from shopify_client import get_orders
from detrack.order_builder import build_delivery_orders

# TEMPORARY: test Shopify → TDB delivery order conversion
orders = get_orders()
delivery_orders = build_delivery_orders(orders)

test_order = delivery_orders[0]

st.write("TDB DELIVERY ORDER")
st.write(test_order)

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
