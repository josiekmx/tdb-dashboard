
import streamlit as st

from procurement.sheets_client import get_flower_recipe_rows


def display_procurement_test():
    st.header("🧪 Test Procurement")
    st.caption("Flower Procurement — Development")

    st.subheader("Step 1: Google Sheets Connection")

    if st.button("🔄 Test Flower Recipe Connection"):
        try:
            rows = get_flower_recipe_rows()

            if not rows:
                st.warning(
                    "Connected successfully, but the Flower Recipe worksheet is empty."
                )
                return

            st.success("Connected to Flower Inventory!")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Recipe Rows",
                    max(len(rows) - 1, 0)
                )

            with col2:
                st.metric(
                    "Flower Columns",
                    max(len(rows[0]) - 1, 0)
                )

            st.subheader("Flower Recipe Preview")

            # Display first 5 recipe rows with headers
            headers = rows[0]
            preview = rows[1:6]

            import pandas as pd

            preview = [
                row[:len(headers)] +
                [""] * max(0, len(headers) - len(row))
                for row in preview
            ]

            st.dataframe(
                pd.DataFrame(preview, columns=headers),
                use_container_width=True,
                hide_index=True,
            )

        except Exception as error:
            st.error(f"Connection failed: {error}")
