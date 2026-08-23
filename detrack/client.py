import streamlit as st


# Load Detrack API key securely from Streamlit Secrets
DETRACK_API_KEY = st.secrets["DETRACK_API_KEY"]


# Build authentication headers for Detrack API requests
def get_detrack_headers():
    return {
        "Content-Type": "application/json",
        "X-API-KEY": DETRACK_API_KEY,
    }