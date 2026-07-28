import requests
import streamlit as st

SHOP = st.secrets["SHOP"]
TOKEN = st.secrets["TOKEN"]

# WARNING: currently limits order retrieval to 250 open orders 
# as this is the maximum records that can be retrieved 
# per request using REST Admin API. Fulfilled, archived, or cancelled
# orders will not be retrieved

# retrieves orders from shopify database
# and returns the latest 250 open orders created
# in json format
def get_orders(limit=250):
    url = f"https://{SHOP}/admin/api/2026-01/orders.json"
    headers = {
        "X-Shopify-Access-Token": TOKEN,
        "Content-Type": "application/json"
    }
    params = {
        "status": "open",
        "limit": limit
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )
    response.raise_for_status()

    return response.json()["orders"]