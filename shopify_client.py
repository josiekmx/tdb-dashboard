import requests
import streamlit as st

SHOP = st.secrets["SHOP"]
TOKEN = st.secrets["TOKEN"]

# WARNING: currently limits order retrieval to 250 open orders 
# as this is the maximum number of records that can be retrieved 
# per request using REST Admin API. Fulfilled, archived, or cancelled
# orders will not be retrieved


ASSIGNEES = {
    "Josie": "tdb_assignee_JOSIE",
    "Enie": "tdb_assignee_ENIE",
    "Puiyee": "tdb_assignee_PUIYEE",
}

ASSIGNEE_TAG_PREFIX = "tdb_assignee_"

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


# updates a specific shopify order with completion status
def update_order_completed(shopify_id, completed):
    url = f"https://{SHOP}/admin/api/2026-01/orders/{shopify_id}.json"
    headers = {
        "X-Shopify-Access-Token": TOKEN,
        "Content-Type": "application/json"
    }

    # retrieves the most updated order data for a specific order 
    # based on the given shopify id
    response = requests.get(
        url,
        headers=headers
    )
    response.raise_for_status()
    order = response.json()["order"]
    tags = [tag.strip() for tag in order["tags"].split(",") if tag.strip()]

    # if order is to be marked as completed,
    # attach a completed tag to the order
    # otherwise, remove any existing completed tag from the order
    COMPLETED_TAG = "tdb_completed"
    if completed:
        if COMPLETED_TAG not in tags:
            tags.append(COMPLETED_TAG)
    else:
        tags = [tag for tag in tags if tag != COMPLETED_TAG]

    updated_tags = ", ".join(tags)
    payload = {
        "order": {
            "id": shopify_id,
            "tags": updated_tags
        }
    }

    # update specific order on shopify with the new updated tag list
    response = requests.put(
        url,
        headers=headers,
        json=payload
    )

    response.raise_for_status()
    return True

    # updates a specific shopify order with an assignee
def update_order_assignee(shopify_id, assignee):
        
        url = f"https://{SHOP}/admin/api/2026-01/orders/{shopify_id}.json"
        
        headers = {
        "X-Shopify-Access-Token": TOKEN,
        "Content-Type": "application/json"
        } 

        # Validate before making any Shopify write
        if assignee is not None and assignee not in ASSIGNEES:
            raise ValueError(f"Invalid assignee: {assignee}")

        # Get latest version of order
        response = requests.get(url,
        headers=headers)

        response.raise_for_status()

        order = response.json()["order"]

        # Get existing tags
        tags = [
            tag.strip()
            for tag in order.get("tags", "").split(",")
            if tag.strip()
        ]

        # Remove only existing assignee tag
        tags = [
            tag for tag in tags
            if not tag.startswith(ASSIGNEE_TAG_PREFIX)
        ]

        # Add new assignee
        if assignee is not None:
        tags.append(ASSIGNEES[assignee])

        updated_tags = ", ".join(tags)

        payload = {
            "order": {
            "id": shopify_id,
            "tags": updated_tags
            }
        }

        response = requests.put(
        url,
        headers=headers,
        json=payload
        )

        response.raise_for_status()

        return True   
        
    