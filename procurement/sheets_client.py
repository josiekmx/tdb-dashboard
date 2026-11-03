
import streamlit as st

from detrack.sku_mapping import get_google_sheets_client


@st.cache_data(ttl=300)
def get_flower_recipe_rows():
    """
    Fetch Flower Recipe from Google Sheets
    using the existing Detrack authentication.
    """

    client = get_google_sheets_client()

    spreadsheet = client.open("Flower Inventory")
    worksheet = spreadsheet.worksheet("Flower Recipe")

    return worksheet.get_all_values()
