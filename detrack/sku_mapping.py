import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


# Create a read-only Google Sheets client using Streamlit Secrets
def get_google_sheets_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]

    credentials = Credentials.from_service_account_info(
        dict(st.secrets["google_service_account"]),
        scopes=scopes
    )

    return gspread.authorize(credentials)


# Read SKU → Tags Required mapping from Google Sheet
def get_sku_tag_mapping():
    client = get_google_sheets_client()

    spreadsheet = client.open("TDB - SKU Tag Mapping")
    worksheet = spreadsheet.worksheet("SKU Tags")

    rows = worksheet.get_all_records()

    mapping = {}

    for row in rows:
        sku = str(row.get("SKU", "")).strip()
        tags_required = row.get("Tags Required")

        if not sku:
            continue

        mapping[sku] = int(tags_required)

    return mapping