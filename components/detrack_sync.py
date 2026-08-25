import pandas as pd
import streamlit as st

from shopify_client import get_orders
from detrack.order_builder import build_delivery_orders
from detrack.sku_mapping import get_sku_tag_mapping
from detrack.tag_calculator import calculate_tags
from detrack.validator import validate_order
from detrack.mapper import (
    map_timeslot_to_detrack,
    map_orders_to_detrack,
)
from detrack.payload_builder import build_detrack_v1_payload
from detrack.client import (
    create_detrack_deliveries,
    get_existing_detrack_order_numbers,
)


# ---------------------------------------------------------
# PREPARE SHOPIFY ORDERS FOR DETRACK
# ---------------------------------------------------------

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
    today = pd.Timestamp.now(
        tz="Asia/Singapore"
    ).date()

    delivery_orders = [
        order
        for order in delivery_orders
        if order.delivery_date
        and pd.to_datetime(order.delivery_date).date() >= today
    ]

    return delivery_orders


# ---------------------------------------------------------
# STATUS DISPLAY
# ---------------------------------------------------------

def style_status(value):
    styles = {
        "PENDING": (
            "background-color: #DCEEFF; "
            "color: #2F6FA5; "
            "font-weight: 600;"
        ),
        "WARNING": (
            "background-color: #FFF3CD; "
            "color: #856404; "
            "font-weight: 600;"
        ),
        "ERROR": (
            "background-color: #F8D7DA; "
            "color: #A94442; "
            "font-weight: 600;"
        ),
        "UPLOADED": (
            "background-color: #DDF2E1; "
            "color: #2E7D45; "
            "font-weight: 600;"
        ),
    }

    return styles.get(value, "")


# ---------------------------------------------------------
# DETRACK SYNC PAGE
# ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # CHECK EXISTING DETRACK ORDERS
    # ---------------------------------------------------------

    try:
        existing_detrack_orders = (
            get_existing_detrack_order_numbers(
                selected_date
            )
        )

    except Exception as e:
        existing_detrack_orders = set()

        st.warning(
            f"Could not check existing Detrack orders: {e}"
        )

    # ---------------------------------------------------------
    # ORDER STATUS TABLE
    # ---------------------------------------------------------

    rows = []

    for order in date_orders:

        # Uploaded takes priority over validation status
        if order.order_number in existing_detrack_orders:
            display_status = "UPLOADED"

        elif order.validation_status == "ERROR":
            display_status = "ERROR"

        elif order.validation_status == "WARNING":
            display_status = "WARNING"

        else:
            # READY internally = PENDING upload in the UI
            display_status = "PENDING"

        rows.append({
            "Issues": ", ".join(
                order.validation_messages
            ),
            "Status": display_status,
            "Order": order.order_number,
            "Type": order.delivery_type,
            "Timeslot": map_timeslot_to_detrack(order),
            "Recipient": order.recipient_name,
            "Tags": order.number_of_tags,
            "Status": display_status,
            "Issues": ", ".join(
                order.validation_messages
            ),
        })

    df = pd.DataFrame(rows)

    # Apply colour styling to Status column
    styled_df = df.style.map(
        style_status,
        subset=["Status"]
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    # ---------------------------------------------------------
    # DETRACK UPLOAD PREVIEW
    # ---------------------------------------------------------

    st.subheader("Detrack Upload Preview")

    # READY and WARNING orders are eligible for upload
    eligible_orders = [
        order
        for order in date_orders
        if order.validation_status in [
            "READY",
            "WARNING"
        ]
    ]

    # Orders already found in Detrack
    already_uploaded_orders = [
        order
        for order in eligible_orders
        if order.order_number in existing_detrack_orders
    ]

    # Orders that have not yet been uploaded
    upload_candidates = [
        order
        for order in eligible_orders
        if order.order_number not in existing_detrack_orders
    ]

    # ---------------------------------------------------------
    # UPLOAD SUMMARY
    # ---------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total in Detrack",
            len(existing_detrack_orders),
            border=True
    )

    with col2:
        st.metric(
            "Already in Detrack",
            len(already_uploaded_orders),
            border=True
        )

    with col3:
        st.metric(
            "Ready to Upload",
            len(upload_candidates),
            border=True
        )

    # ---------------------------------------------------------
    # UPLOAD PREVIEW TABLE
    # ---------------------------------------------------------

    if upload_candidates:
        detrack_rows = map_orders_to_detrack(
            upload_candidates
        )

        detrack_df = pd.DataFrame(
            detrack_rows
        )

        # Only show useful Detrack columns
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

        detrack_preview_df = detrack_df[
            preview_columns
        ]

        st.dataframe(
            detrack_preview_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "No new orders are currently available "
            "for Detrack upload."
        )

    # ---------------------------------------------------------
    # BATCH UPLOAD
    # ---------------------------------------------------------

    if upload_candidates:
        batch_payloads = []

        # Build one Detrack payload per order
        for order in upload_candidates:
            timeslot_label = (
                map_timeslot_to_detrack(order)
            )

            payload = build_detrack_v1_payload(
                order,
                timeslot_label
            )

            batch_payloads.append(payload)

        st.subheader("Upload to Detrack")

        st.write(
            f"{len(batch_payloads)} new order(s) "
            f"ready to upload."
        )

        if st.button(
            f"Upload {len(batch_payloads)} "
            f"New Orders to Detrack",
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

                # Rerun so newly uploaded orders
                # immediately change to UPLOADED
                st.rerun()

            except Exception as e:
                st.error(
                    f"Detrack batch upload failed: {e}"
                )