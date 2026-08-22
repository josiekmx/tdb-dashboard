# Display Detrack orders by selected delivery date
def display_detrack_sync():
    st.subheader("Detrack Sync")

    delivery_orders = prepare_detrack_orders()

    # Get available dates and default to the earliest
    available_dates = sorted({
        order.delivery_date
        for order in delivery_orders
        if order.delivery_date
    })

    if not available_dates:
        st.info("No upcoming orders found.")
        return

    selected_date = st.selectbox(
        "Delivery / Pickup Date",
        available_dates
    )

    # Only show orders for the selected date
    date_orders = [
        order
        for order in delivery_orders
        if order.delivery_date == selected_date
    ]

    rows = []

    for order in date_orders:
        rows.append({
            "Order": order.order_number,
            "Type": order.delivery_type,
            "Timeslot": map_timeslot_to_detrack(order),
            "Recipient": order.recipient_name,
            "Tags": order.number_of_tags,
            "Status": order.validation_status,
            "Issues": ", ".join(order.validation_messages),
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )