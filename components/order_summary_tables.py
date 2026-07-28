import streamlit as st

def display_order_summary_tables(filtered):
    delivery_orders = filtered[filtered["Delivery Type"] == "Delivery"]
    pickup_orders = filtered[filtered["Delivery Type"] == "Pickup"]
    missing_delivery_orders = filtered[filtered["Delivery Type"].isna()]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Deliveries")
        st.metric("Total Orders", len(delivery_orders))

        delivery_summary = (
            delivery_orders.groupby("SKU")
            .size()
            .reset_index(name="Count")
            .sort_values("SKU")
        )

        st.dataframe(
            delivery_summary,
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.markdown("### Pickups")
        st.metric("Total Orders", len(pickup_orders))

        pickup_summary = (
            pickup_orders.groupby("SKU")
            .size()
            .reset_index(name="Count")
            .sort_values("SKU")
        )

        st.dataframe(
            pickup_summary,
            use_container_width=True,
            hide_index=True
        )

    with col3:
        st.markdown("### Missing Delivery Type")
        st.metric("Total Orders", len(missing_delivery_orders))

        missing_delivery_summary = (
            missing_delivery_orders.groupby("SKU")
            .size()
            .reset_index(name="Count")
            .sort_values("SKU")
        )

        st.dataframe(
            missing_delivery_summary,
            use_container_width=True,
            hide_index=True
        )