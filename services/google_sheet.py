import pandas as pd
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

if "gcp_service_account" in st.secrets:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
else:
    creds = Credentials.from_service_account_file(
        "service_account.json",
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