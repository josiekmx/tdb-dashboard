import streamlit as st
from order_processor import process_orders
from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables

# displays login page to authenticate users
if not check_password():
    st.stop()

# set windows tab
st.set_page_config(
    page_title="The Daily Blooms Dashboard",
    page_icon="🌸",
    layout="wide"
)

# dashboard header
st.header("The Daily Blooms Dashboard 🌸")

# order_details_table
filtered = display_order_details_table()

# summary tables 
display_order_summary_tables()
