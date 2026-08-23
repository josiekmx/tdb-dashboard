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

# Get order numbers already uploaded to Detrack for one date
def get_existing_detrack_order_numbers(date):
    result = test_detrack_connection(date)

    deliveries = result.get("deliveries", [])

    return {
        delivery.get("do")
        for delivery in deliveries
        if delivery.get("do")
    }

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


# Upload multiple deliveries to Detrack in batches of up to 100
def create_detrack_deliveries(payloads):
    url = "https://app.detrack.com/api/v1/deliveries/create.json"

    batch_size = 100
    results = []

    for i in range(0, len(payloads), batch_size):
        batch = payloads[i:i + batch_size]

        response = requests.post(
            url,
            headers=get_detrack_headers(),
            json=batch,
            timeout=30,
        )

        response.raise_for_status()

        results.append(response.json())

    return results    