import streamlit as st


# Build SKU summary split by ribbon / no ribbon
def build_sku_summary(orders):
    if orders.empty:
        return orders[["SKU"]].assign(
            **{
                "No Ribbon": 0,
                "Ribbon": 0,
            }
        )

    summary = (
        orders.groupby(["SKU", "Ribbon"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Ensure both Ribbon categories exist
    if False not in summary.columns:
        summary[False] = 0

    if True not in summary.columns:
        summary[True] = 0

    # Rename for display
    summary = summary.rename(
        columns={
            False: "No Ribbon",
            True: "Ribbon",
        }
    )

    # Calculate total temporarily for sorting
    summary["_Total"] = (
        summary["No Ribbon"]
        + summary["Ribbon"]
    )

    # Highest total quantity first
    summary = summary.sort_values(
        by=["_Total", "SKU"],
        ascending=[False, True]
    )

    # Remove temporary total column
    summary = summary.drop(columns=["_Total"])

    return summary[
        ["SKU", "No Ribbon", "Ribbon"]
    ]


def display_order_summary_tables(filtered):
    delivery_orders = filtered[
        filtered["Delivery Type"] == "Delivery"
    ]

    pickup_orders = filtered[
        filtered["Delivery Type"] == "Pickup"
    ]

    col1, col2 = st.columns(2)

    # -------------------------
    # Deliveries
    # -------------------------
    with col1:
        st.markdown("### Deliveries")
        st.metric(
            "Total Orders",
            len(delivery_orders)
        )

        delivery_summary = build_sku_summary(
            delivery_orders
        )

        st.dataframe(
            delivery_summary,
            use_container_width=True,
            hide_index=True
        )

    # -------------------------
    # Pickups
    # -------------------------
    with col2:
        st.markdown("### Pickups")
        st.metric(
            "Total Orders",
            len(pickup_orders)
        )

        pickup_summary = build_sku_summary(
            pickup_orders
        )

        st.dataframe(
            pickup_summary,
            use_container_width=True,
            hide_index=True
        )