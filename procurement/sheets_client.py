
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


@st.cache_data(ttl=300)
def get_flower_recipe_rows():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]

    credentials = Credentials.from_service_account_info(
        dict(st.secrets["google_service_account"]),
        scopes=scopes,
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open("Flower Inventory")
    worksheet = spreadsheet.worksheet("Flower Recipe")

    return worksheet.get_all_values()
