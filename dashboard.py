import streamlit as st
from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables
from shopify_client import get_orders

# TEMPORARY: locate where additional request / remarks are stored
orders = get_orders()

for order in orders[:30]:

    if order.get("note"):
        st.write("ORDER HAS NOTE")

    for attr in order.get("note_attributes", []):
        st.write("NOTE ATTRIBUTE:", attr.get("name"))

    for item in order.get("line_items", []):
        for prop in item.get("properties", []):
            name = prop.get("name")

            if any(word in str(name).lower() for word in [
                "request",
                "remark",
                "instruction",
                "note",
                "additional"
            ]):
                st.write("LINE ITEM PROPERTY:", name)

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
