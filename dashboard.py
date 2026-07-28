import streamlit as st
from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables

# displays login page to authenticate users
if not check_password():
    st.stop()

# set windows tab
st.set_page_config(
    page_title="The Daily Blooms Dashboard",
    page_icon="assets/flower_logo2.png",
    layout="wide"
)

# dashboard header
col1, col2 = st.columns([0.08, 0.92])

with col1:
    st.image("assets/flower_logo2.png", width=120)

with col2:
    st.header("The Daily Blooms Dashboard")

# enables refresh
# upon refresh, the date and timeslots will return to 
# default state of the earliest date and all timeslots respectively. 
if st.button("Refresh"):
    # Reset filters
    st.session_state.selected_date = None
    st.session_state.selected_slots = []

    st.rerun()

# order details table
filtered_table_data = display_order_details_table()

# summary tables 
display_order_summary_tables(filtered_table_data)
