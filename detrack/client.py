import requests
import streamlit as st


DETRACK_API_KEY = st.secrets["DETRACK_API_KEY"]


# Build authentication headers for Detrack API
def get_detrack_headers():
    return {
        "Content-Type": "application/json",
        "X-API-KEY": DETRACK_API_KEY,
    }


# Read Detrack deliveries for one date without creating anything
def test_detrack_connection(date):
    url = "https://app.detrack.com/api/v1/deliveries/view/all.json"

    response = requests.post(
        url,
        headers=get_detrack_headers(),
        json={"date": date},
        timeout=20,
    )

    response.raise_for_status()

    return response.json()

# Create Detrack deliveries for one date 
def create_detrack_delivery(payload):
    url = "https://app.detrack.com/api/v1/deliveries/create.json"

    response = requests.post(
        url,
        headers=get_detrack_headers(),

        # Detrack create endpoint expects an array of deliveries
        json=[payload],

        timeout=20,
    )

    response.raise_for_status()

    return response.json()    