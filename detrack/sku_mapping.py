import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


# Create a read-only Google Sheets client
def get_google_sheets_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    credentials = Credentials.from_service_account_info(
        dict(st.secrets["google_service_account"]),
        scopes=scopes
    )

    return gspread.authorize(credentials)


# Read SKU → Tags Required mapping from Google Sheet
def get_sku_tag_mapping():
    client = get_google_sheets_client()

    spreadsheet = client.open("SKU Mapping")
    worksheet = spreadsheet.worksheet("SKU Tags")

    # TEMPORARY: inspect what Google Sheets is returning
    st.write("HEADERS:", worksheet.row_values(1))
    st.write("FIRST 5 RAW ROWS:", worksheet.get_all_values()[:5])

    rows = worksheet.get_all_records()

    mapping = {}

    for row in rows:
        sku = str(row.get("SKU", "")).strip().upper()
        tags_required = row.get("Tags Required")

        if not sku or tags_required in (None, ""):
            continue

        mapping[sku] = int(tags_required)

    return mapping