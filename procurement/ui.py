
import pandas as pd
import streamlit as st

from procurement.sheets_client import get_flower_recipe_rows
from procurement.recipes import lookup_recipe
from datetime import date, timedelta
from shopify_client import get_orders
from procurement.order_demand import build_order_demand


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



    # ---------------------------------------
    # Stage 3: Shopify Order Demand
    # ---------------------------------------

    st.divider()
    st.subheader("📦 Stage 3: Shopify Order Demand")

    st.caption(
        "Preliminary test: uses the existing Shopify REST "
        "function, limited to up to 250 open orders."
    )

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Delivery Date From",
            value=date.today(),
            key="procurement_start_date",
        )

    with col2:
        end_date = st.date_input(
            "Delivery Date To",
            value=date.today() + timedelta(days=7),
            key="procurement_end_date",
        )

    if st.button("🔄 Pull Shopify Demand"):
        if start_date > end_date:
            st.error("End date must be on or after start date.")
        else:
            try:
                with st.spinner("Fetching Shopify orders..."):
                    orders = get_orders()

                    result = build_order_demand(
                        orders,
                        start_date,
                        end_date,
                    )

                st.warning(
                    "Preliminary demand only. Archived orders "
                    "and pagination are not yet included."
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Orders in Date Range",
                    result["orders_count"],
                )

                col2.metric(
                    "Outstanding Units",
                    result["total_outstanding"],
                )

                col3.metric(
                    "Warnings",
                    len(result["warnings"]),
                )

                st.subheader("Outstanding SKU Demand")

                if result["demand_rows"]:
                    st.dataframe(
                        pd.DataFrame(result["demand_rows"]),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info(
                        "No outstanding SKU demand found "
                        "in the fetched orders."
                    )

                if result["warnings"]:
                    with st.expander(
                        "⚠️ Orders Requiring Review"
                    ):
                        st.dataframe(
                            pd.DataFrame(result["warnings"]),
                            use_container_width=True,
                            hide_index=True,
                        )

            except Exception as error:
                st.error(
                    f"Shopify demand test failed: {error}"
                )

