import streamlit as st
from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables

# TEMPORARY: inspect Shopify order structure without exposing customer values
orders = get_orders()
test_order = orders[0]

# Display available top-level Shopify order fields
st.write("ORDER FIELDS")
st.write(list(test_order.keys()))

# Display product property names used by Shopify
st.write("LINE ITEM PROPERTIES")

for item in test_order.get("line_items", []):
    st.write("Product:", item.get("title"))

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
