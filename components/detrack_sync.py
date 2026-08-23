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
    create_detrack_deliveries,
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
     # ---------------------------------------------------------
    # Detrack Upload Preview
    # ---------------------------------------------------------
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

    # Show upload summary as metric cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Orders",
            len(eligible_orders)
        )

    with col2:
        st.metric(
            "Already in Detrack",
            len(already_uploaded_orders)
        )

    with col3:
        st.metric(
            "Ready to Upload",
            len(upload_candidates)
        )

    # Only build upload preview when eligible orders exist
    if upload_candidates:
        detrack_rows = map_orders_to_detrack(upload_candidates)
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
        st.info(
            "No new orders are currently available for Detrack upload."
        )


    # ---------------------------------------------------------
    # UPLOAD BUTTON - BATCH UPLOAD: ALL NEW ORDERS FOR SELECTED DATE
    # ---------------------------------------------------------

    if upload_candidates:
        batch_payloads = []

        # Build one Detrack payload per order
        for order in upload_candidates:
            timeslot_label = map_timeslot_to_detrack(order)

            payload = build_detrack_v1_payload(
                order,
                timeslot_label
            )

            batch_payloads.append(payload)

        st.subheader("Upload to Detrack")

        st.write(
            f"{len(batch_payloads)} new order(s) ready to upload."
        )

        if st.button(
            f"Upload {len(batch_payloads)} New Orders to Detrack",
            type="primary"
        ):
            try:
                results = create_detrack_deliveries(
                    batch_payloads
                )

                st.success(
                    f"Upload completed for "
                    f"{len(batch_payloads)} order(s)."
                )

                # Show Detrack response for each batch
                for batch_number, result in enumerate(
                    results,
                    start=1
                ):
                    st.write(
                        f"Batch {batch_number}"
                    )
                    st.json(result)

                # Refresh so newly uploaded orders are detected
                # by the duplicate checker
                st.rerun()

            except Exception as e:
                st.error(
                    f"Detrack batch upload failed: {e}"
                )            