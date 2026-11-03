
import streamlit as st
from procurement.sheets_client import get_flower_recipe_rows

st.title("Flower Recipe Connection Test")

try:
    rows = get_flower_recipe_rows()

    st.success("Connected to Flower Inventory!")
    st.write("Total rows:", len(rows))
    st.write("Total columns:", len(rows[0]) if rows else 0)

    st.subheader("First 5 rows")
    st.dataframe(rows[:5])

except Exception as error:
    st.error(f"Connection failed: {error}")
