import streamlit as st

def display_order_summary_tables(filtered):
    delivery_orders = filtered[filtered["Delivery Type"] == "Delivery"]
    pickup_orders = filtered[filtered["Delivery Type"] == "Pickup"]

    col1, col2 = st.columns(2)

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
        st.markdown("### Pickupss")
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