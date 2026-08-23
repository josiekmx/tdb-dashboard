import pandas as pd
import streamlit as st

from shopify_client import get_orders
from detrack.order_builder import build_delivery_orders
from detrack.sku_mapping import get_sku_tag_mapping
from detrack.tag_calculator import calculate_tags
from detrack.validator import validate_order
from detrack.mapper import map_timeslot_to_detrack, map_orders_to_detrack
from detrack.payload_builder import build_detrack_payload
from detrack.payload_builder import build_detrack_v1_payload
from detrack.client import (
    test_detrack_connection,
    create_detrack_delivery,
    get_existing_detrack_order_numbers,
)


# Build and validate upcoming unfulfilled Shopify orders for Detrack
def prepare_detrack_orders():
    orders = get_orders()

    # Only keep orders that are not fully fulfilled
    unfulfilled_orders = [
        order
        for order in orders
        if order.get("fulfillment_status") != "fulfilled"
    ]

    delivery_orders = build_delivery_orders(unfulfilled_orders)
    sku_mapping = get_sku_tag_mapping()

    # Calculate tag quantity and validate each order
    for order in delivery_orders:
        total_tags, missing_skus = calculate_tags(
            order,
            sku_mapping
        )

        order.number_of_tags = total_tags
        validate_order(order, missing_skus)

    # Only keep delivery / pickup dates from today onwards
    today = pd.Timestamp.now(tz="Asia/Singapore").date()

    delivery_orders = [
        order
        for order in delivery_orders
        if order.delivery_date
        and pd.to_datetime(order.delivery_date).date() >= today
    ]

    return delivery_orders


# Display Detrack orders by selected delivery / pickup date
def display_detrack_sync():
    st.subheader("Detrack Sync")

    delivery_orders = prepare_detrack_orders()

    # Get available upcoming order dates
    available_dates = sorted({
        order.delivery_date
        for order in delivery_orders
        if order.delivery_date
    })

    if not available_dates:
        st.info("No upcoming unfulfilled orders found.")
        return

    # Select which date to prepare for Detrack
    selected_date = st.selectbox(
        "Delivery / Pickup Date",
        available_dates
    )

    # Keep only orders for selected date
    date_orders = [
        order
        for order in delivery_orders
        if order.delivery_date == selected_date
    ]

    rows = []

    # Build Detrack preview
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

    # Preview only READY and WARNING orders that are eligible for Detrack upload
    st.subheader("Detrack Upload Preview")

    eligible_orders = [
        order
        for order in date_orders
        if order.validation_status in ["READY", "WARNING"]
    ]

    # Check which orders already exist in Detrack for the selected date
    try:
        existing_detrack_orders = get_existing_detrack_order_numbers(
            selected_date
        )
    except Exception as e:
        existing_detrack_orders = set()

        st.warning(
            f"Could not check existing Detrack orders: {e}"
        )

    # Separate already-uploaded orders from new orders
    already_uploaded_orders = [
        order
        for order in eligible_orders
        if order.order_number in existing_detrack_orders
    ]

    upload_candidates = [
        order
        for order in eligible_orders
        if order.order_number not in existing_detrack_orders
    ]

    # Only build upload preview when eligible orders exist
    if eligible_orders:
        detrack_rows = map_orders_to_detrack(eligible_orders)
        detrack_df = pd.DataFrame(detrack_rows)

    # Hide permanently unused Detrack columns from preview
        preview_columns = [
            "Assign to",
            "Order ID",
            "Delivery Date",
            "Delivery Timeslot",
            "Delivery Address",
            "Postal Code",
            "Recipient's Name",
            "Recipient Number",
            "Sender's Contact",
            "Notes",
            "Sender Email",
            "Sender Name",
            "Group",
            "No. of tags",
            "SKU",
            "Item Description",
            "Quantity",
        ]

        detrack_preview_df = detrack_df[preview_columns]

        st.dataframe(
            detrack_preview_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning(
            "No orders are currently eligible for Detrack upload."
        )


    # TEMPORARY: preview one API payload without sending it
    if eligible_orders:
        test_order = eligible_orders[0]

        test_payload = build_detrack_payload(
            test_order,
            map_timeslot_to_detrack(test_order)
        )

        st.subheader("API Payload Test")
        st.json(test_payload)


    # TEMPORARY: test Detrack API authentication without creating jobs
    if st.button("Test Detrack Connection"):
        try:
            result = test_detrack_connection(selected_date)

            st.success("Detrack connection successful")
            st.write(result)

        except Exception as e:
            st.error(f"Detrack connection failed: {e}")    

    # TEST ONLY: choose one eligible order and upload it to Detrack
    if eligible_orders:
        order_options = {
            order.order_number: order
            for order in eligible_orders
        }

        selected_test_order_number = st.selectbox(
            "Select one order for Detrack test upload",
            list(order_options.keys())
        )

        selected_test_order = order_options[selected_test_order_number]

        if st.button(f"Upload Test: {selected_test_order_number}"):
            try:
                timeslot_label = map_timeslot_to_detrack(selected_test_order)

                payload = build_detrack_v1_payload(
                    selected_test_order,
                    timeslot_label
                )

                result = create_detrack_delivery(payload)

                st.success(
                    f"{selected_test_order_number} uploaded to Detrack"
                )

                st.json(result)

            except Exception as e:
                st.error(f"Detrack upload failed: {e}")