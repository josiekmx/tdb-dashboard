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

# Main dashboard sections
orders_tab, detrack_tab = st.tabs([
    "Orders",
    "Detrack Sync"
])

with orders_tab:
    # order details table
    filtered_table_data = display_order_details_table()

    # summary tables 
    display_order_summary_tables(filtered_table_data)

with detrack_tab:
    display_detrack_sync()

# enables refresh
# upon refresh, the date and timeslots will return to 
# default state of the earliest date and all timeslots respectively. 
#if st.button("Refresh"):
    # Reset filters
    #st.session_state.selected_date = None
    #st.session_state.selected_slots = []
    #st.rerun()

# Refresh dashboard data without modifying active widget state
if st.button("Refresh"):
    st.rerun()

# insert empty space to optimise ui
st.markdown("<br>", unsafe_allow_html=True)



