import pandas as pd
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )

client = gspread.authorize(creds)
sheet = client.open("The Daily Blooms Dashboard Data").worksheet("Assignments")

def load_assignments():
    records = sheet.get_all_records()

    if not records:
        return pd.DataFrame(
            columns=[
                "Order",
                "Assignee",
                "Completed"
            ]
        )

    return pd.DataFrame(records)

def sync_orders(shopify_df):
    """
    Synchronise the Assignments sheet with Shopify.

    - Adds new Shopify orders
    - Removes orders no longer in Shopify
    - Preserves Assignee and Completed values
    """

    existing = load_assignments()

    # Current Shopify orders
    shopify_orders = set(shopify_df["Order"])

    # Keep only orders that still exist
    if not existing.empty:
        existing = existing[existing["Order"].isin(shopify_orders)]

    existing_orders = set(existing["Order"]) if not existing.empty else set()

    # Add any new Shopify orders
    new_rows = []
    for order in shopify_df["Order"]:
        if order not in existing_orders:
            new_rows.append({
                "Order": order,
                "Assignee": "",
                "Completed": False
            })

    if new_rows:
        existing = pd.concat(
            [existing, pd.DataFrame(new_rows)],
            ignore_index=True
        )

    # Keep the same order as Shopify
    existing["Order"] = pd.Categorical(
        existing["Order"],
        categories=shopify_df["Order"],
        ordered=True
    )
    existing = existing.sort_values("Order")

    # Rewrite the worksheet
    sheet.clear()
    sheet.append_row(existing.columns.tolist())
    sheet.append_rows(existing.values.tolist())


def save_assignments(assignments_df):
    """
    Replace the Assignments sheet with the edited assignments.
    """

    sheet.clear()

    sheet.append_row(assignments_df.columns.tolist())

    sheet.append_rows(assignments_df.values.tolist())