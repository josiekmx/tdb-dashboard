
import streamlit as st

from detrack.sku_mapping import get_google_client


@st.cache_data(ttl=300)
def get_flower_recipe_rows():
    """
    Read the Flower Recipe worksheet using the
    existing Detrack Google Sheets connection.
    """
    client = get_google_client()

    spreadsheet = client.open("Flower Inventory")
    worksheet = spreadsheet.worksheet("Flower Recipe")

    return worksheet.get_all_values()
