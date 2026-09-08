import requests
import streamlit as st

SHOP = st.secrets["SHOP"]
TOKEN = st.secrets["TOKEN"]

# WARNING: currently limits order retrieval to 250 open orders
# as this is the maximum number of records that can be retrieved
# per request using REST Admin API. Fulfilled, archived, or cancelled
# orders will not be retrieved


ASSIGNEES = {
    "Enie": "tdb_assignee_ENIE",
    "Puiyee": "tdb_assignee_PUIYEE",
    "Justin": "tdb_assignee_JUSTIN",
    "Josie": "tdb_assignee_JOSIE",
    "Sophia": "tdb_assignee_SOPHIA",
    "Natalie": "tdb_assignee_NATALIE",
    "Christy": "tdb_assignee_CHRISTY",
    "Qianhui": "tdb_assignee_QIANHUI",
    "Zephyr": "tdb_assignee_ZEPHYR"
}

ASSIGNEE_TAG_PREFIX = "tdb_assignee_"


# Retrieves orders from Shopify database
# and returns the latest 250 open orders created
# in JSON format
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


# TESTING / POLAROID:
# Retrieves one Shopify order through GraphQL
# including both direct line item properties and
# Giftship Bundle Line Properties
def get_order_graphql(shopify_order_id):
    url = f"https://{SHOP}/admin/api/2026-01/graphql.json"

    headers = {
        "X-Shopify-Access-Token": TOKEN,
        "Content-Type": "application/json"
    }

    graphql_order_id = f"gid://shopify/Order/{shopify_order_id}"

    query = """
    query GetOrder($id: ID!) {
        order(id: $id) {
            id
            name

            lineItems(first: 100) {
                nodes {
                    id
                    name
                    title
                    sku
                    quantity

                    customAttributes {
                        key
                        value
                    }

                    lineItemGroup {
                        id
                        title
                        quantity

                        customAttributes {
                            key
                            value
                        }
                    }
                }
            }
        }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "id": graphql_order_id
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    response.raise_for_status()

    data = response.json()

    # GraphQL may return HTTP 200 even when query contains errors
    if data.get("errors"):
        raise Exception(data["errors"])

    return data["data"]["order"]


# Updates a specific Shopify order with completion status
def update_order_completed(shopify_id, completed):
    url = f"https://{SHOP}/admin/api/2026-01/orders/{shopify_id}.json"

    headers = {
        "X-Shopify-Access-Token": TOKEN,
        "Content-Type": "application/json"
    }

    # Retrieves the most updated order data for a specific order
    # based on the given Shopify ID
    response = requests.get(
        url,
        headers=headers
    )

    response.raise_for_status()

    order = response.json()["order"]

    tags = [
        tag.strip()
        for tag in order["tags"].split(",")
        if tag.strip()
    ]

    # If order is to be marked as completed,
    # attach a completed tag to the order.
    # Otherwise remove any existing completed tag.
    COMPLETED_TAG = "tdb_completed"

    if completed:
        if COMPLETED_TAG not in tags:
            tags.append(COMPLETED_TAG)
    else:
        tags = [
            tag
            for tag in tags
            if tag != COMPLETED_TAG
        ]

    updated_tags = ", ".join(tags)

    payload = {
        "order": {
            "id": shopify_id,
            "tags": updated_tags
        }
    }

    # Update specific order on Shopify
    # with the new updated tag list
    response = requests.put(
        url,
        headers=headers,
        json=payload
    )

    response.raise_for_status()

    return True


# Updates a specific Shopify order with an assignee
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
    response = requests.get(
        url,
        headers=headers
    )

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
        tag
        for tag in tags
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