
import pandas as pd
import streamlit as st

from procurement.sheets_client import get_flower_recipe_rows
from procurement.recipes import lookup_recipe


def display_procurement_test():
    st.header("🧪 Test Procurement")
    st.caption("Flower Procurement — Development")

    # ---------------------------------------
    # Stage 1: Google Sheets Connection
    # ---------------------------------------

    with st.expander(
        "✅ Stage 1: Google Sheets Connection",
        expanded=False,
    ):
        if st.button("🔄 Test Flower Recipe Connection"):
            try:
                rows = get_flower_recipe_rows()

                if not rows:
                    st.warning("Flower Recipe worksheet is empty.")
                else:
                    st.success("Connected to Flower Inventory!")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Recipe Rows",
                            max(len(rows) - 1, 0),
                        )

                    with col2:
                        st.metric(
                            "Flower Columns",
                            max(len(rows[0]) - 1, 0),
                        )

                    st.subheader("Recipe Preview")

                    headers = rows[0]
                    preview = rows[1:6]

                    preview = [
                        row[:len(headers)]
                        + [""] * max(
                            0, len(headers) - len(row)
                        )
                        for row in preview
                    ]

                    st.dataframe(
                        pd.DataFrame(
                            preview,
                            columns=headers,
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

            except Exception as error:
                st.error(f"Connection failed: {error}")

    # ---------------------------------------
    # Stage 2: SKU Lookup
    # ---------------------------------------

    st.subheader("🔎 Stage 2: SKU Recipe Lookup")

    sku = st.text_input(
        "Search Shopify SKU",
        value="Basket-Pink",
        placeholder="Enter SKU",
    )

    if st.button("Search Recipe", type="primary"):
        try:
            result = lookup_recipe(sku)
            status = result["status"]
            matches = result["matches"]

            if status == "empty_search":
                st.warning("Please enter a SKU.")
                return

            if status == "not_found":
                st.error(f"SKU '{sku}' not found.")
                return

            if status == "duplicate":
                st.warning(
                    f"Duplicate SKU found: {len(matches)} rows. "
                    "Review the Google Sheet before procurement."
                )

            for recipe in matches:
                st.markdown(
                    f"**SKU:** {recipe['sku']} "
                    f"— Google Sheet Row {recipe['sheet_row']}"
                )

                if recipe["issues"]:
                    for issue in recipe["issues"]:
                        st.error(issue)

                if not recipe["has_recipe"]:
                    st.info(
                        "No flower recipe assigned to this SKU."
                    )
                    continue

                flower_data = [
                    {
                        "Flower": flower,
                        "Quantity per Product": (
                            int(quantity)
                            if quantity.is_integer()
                            else quantity
                        ),
                    }
                    for flower, quantity
                    in recipe["flowers"].items()
                ]

                st.dataframe(
                    pd.DataFrame(flower_data),
                    use_container_width=True,
                    hide_index=True,
                )

                st.metric(
                    "Total Flower Stems / Units",
                    sum(recipe["flowers"].values()),
                )

        except Exception as error:
            st.error(f"SKU lookup failed: {error}")
