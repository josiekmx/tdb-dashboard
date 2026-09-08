import io
import re
import zipfile

import requests
import streamlit as st

from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables
from components.detrack_sync import display_detrack_sync

from shopify_client import get_orders, get_order_graphql
from polaroid.queue import build_polaroid_queue
from datetime import datetime
from detrack.client import get_existing_detrack_order_numbers
from components.detrack_sync import style_status


# ----------------------- POLAROID HELPERS -----------------------

def get_image_extension(content_type, photo_url):
    """
    Determine a suitable extension for a downloaded image.
    """

    content_type = (
        str(content_type or "")
        .split(";")[0]
        .strip()
        .lower()
    )

    extension_map = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/heic": "heic",
        "image/heif": "heif",
    }

    if content_type in extension_map:
        return extension_map[content_type]

    clean_url = str(photo_url or "").split("?")[0].lower()

    for extension in [
        "jpg",
        "jpeg",
        "png",
        "webp",
        "heic",
        "heif",
    ]:
        if clean_url.endswith(f".{extension}"):
            if extension == "jpeg":
                return "jpg"

            return extension

    return "jpg"


def clean_filename_part(value):
    """
    Convert text into a safe filename component.
    """

    value = str(value or "").strip()

    replacements = {
        "#": "",
        "/": "-",
        "\\": "-",
        ":": "-",
        "*": "",
        "?": "",
        '"': "",
        "<": "",
        ">": "",
        "|": "-",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = "_".join(value.split())

    return value or "Unknown"


def get_order_number(order_name):
    """
    Extract numeric portion from an order name.

    Example:
        #TDB94103 -> 94103
    """

    match = re.search(
        r"(\d+)",
        str(order_name or "")
    )

    if not match:
        return 999999999

    return int(match.group(1))


def get_polaroid_id(polaroid):
    """
    Create a stable identifier for one Polaroid queue row.

    One separate upload record = one Polaroid.
    """

    return "|".join([
        str(polaroid.get("shopify_id") or ""),
        str(polaroid.get("line_item_id") or ""),
        str(polaroid.get("bundle_group_id") or ""),
        str(polaroid.get("source") or ""),
        str(polaroid.get("photo_url") or ""),
    ])


def build_polaroid_filename(polaroid, sequence):
    """
    Build a unique filename for one Polaroid.
    """

    order_name = clean_filename_part(
        polaroid.get("order")
    )

    recipient = clean_filename_part(
        polaroid.get("recipient")
    )

    source = clean_filename_part(
        polaroid.get("source")
    )

    return (
        f"{sequence:02d}_"
        f"{order_name}_"
        f"{recipient}_"
        f"{source}"
    )


def fetch_polaroid_image(photo_url):
    """
    Download one Polaroid image from Shopify CDN.
    """

    response = requests.get(
        photo_url,
        timeout=30
    )

    response.raise_for_status()

    content_type = (
        response.headers
        .get("Content-Type", "")
        .split(";")[0]
        .strip()
        .lower()
    )

    if not content_type.startswith("image/"):
        raise ValueError(
            "URL did not return an image. "
            f"Content-Type: {content_type}"
        )

    image_bytes = response.content

    if not image_bytes:
        raise ValueError(
            "Downloaded image was empty."
        )

    extension = get_image_extension(
        content_type,
        photo_url
    )

    return (
        image_bytes,
        content_type,
        extension
    )


def prepare_selected_polaroids(polaroids, delivery_date):
    """
    Download selected Polaroids and create one ZIP.

    Selected rows are sorted by Shopify order number
    before 01_, 02_, 03_ numbering is assigned.
    """

    sorted_polaroids = sorted(
        polaroids,
        key=lambda row: (
            get_order_number(
                row.get("order")
            ),
            str(
                row.get("line_item_id")
                or ""
            ),
            str(
                row.get("bundle_group_id")
                or ""
            ),
        )
    )

    zip_buffer = io.BytesIO()

    successful = []
    failed = []

    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED
    ) as zip_file:

        for sequence, polaroid in enumerate(
            sorted_polaroids,
            start=1
        ):
            try:
                photo_url = polaroid.get(
                    "photo_url"
                )

                (
                    image_bytes,
                    content_type,
                    extension
                ) = fetch_polaroid_image(
                    photo_url
                )

                filename_base = (
                    build_polaroid_filename(
                        polaroid,
                        sequence
                    )
                )

                filename = (
                    f"{filename_base}."
                    f"{extension}"
                )

                zip_file.writestr(
                    filename,
                    image_bytes
                )

                successful.append({
                    "order": polaroid.get(
                        "order"
                    ),
                    "recipient": polaroid.get(
                        "recipient"
                    ),
                    "filename": filename,
                })

            except Exception as e:
                failed.append({
                    "order": polaroid.get(
                        "order"
                    ),
                    "recipient": polaroid.get(
                        "recipient"
                    ),
                    "error": str(e),
                })

    zip_buffer.seek(0)

    return {
        "bytes": zip_buffer.getvalue(),
        "filename": (
            f"TDB_Polaroids_"
            f"{clean_filename_part(delivery_date)}"
            f".zip"
        ),
        "delivery_date": delivery_date,
        "requested": len(sorted_polaroids),
        "successful": successful,
        "failed": failed,
    }

def format_purchase_time(value):
    """
    Format Shopify order creation time for display.
    """

    if not value:
        return "—"

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        return dt.strftime(
            "%d %b %Y, %I:%M %p"
        ).lstrip("0")

    except Exception:
        return str(value)

# ----------------------- POLAROID PRINTING -----------------------

def display_polaroid_printing():
    st.subheader("Polaroid Printing")

    # ---------------- LOAD QUEUE ----------------

    if "polaroid_queue" not in st.session_state:
        with st.spinner("Loading Polaroids..."):
            st.session_state["polaroid_queue"] = build_polaroid_queue()

    queue = st.session_state["polaroid_queue"]

    if not queue:
        st.info("No upcoming Polaroids.")
        return

        queue = st.session_state.get(
            "polaroid_queue"
        )

        if queue is None:
            return

        if not queue:
            st.success(
                "No Polaroids currently detected."
            )
            return

    # ---------------- DELIVERY DATE ----------------


    delivery_dates = sorted({
        str(polaroid.get("delivery_date"))
        for polaroid in queue
        if polaroid.get("delivery_date")
    })

    if not delivery_dates:
        st.warning(
            "Polaroids were detected, but none "
            "have a delivery date."
        )
        return

    selected_date = st.selectbox(
        "Delivery Date",
        options=delivery_dates,
        key="polaroid_delivery_date"
    )

    # Check which orders already exist in Detrack
    try:
        existing_detrack_orders = (
            get_existing_detrack_order_numbers(
                selected_date
            )
        )
    except Exception:
        existing_detrack_orders = set()

    date_polaroids = [
        polaroid
        for polaroid in queue
        if str(
            polaroid.get("delivery_date")
        ) == selected_date
    ]



    # Sort table by Shopify order number.
    date_polaroids = sorted(
        date_polaroids,
        key=lambda row: get_order_number(
            row.get("order")
        ),
        reverse=True
    )

    # ---------------- SELECTION STATE ----------------

    st.subheader("Select Orders")

    current_date_state = (
        st.session_state.get(
            "polaroid_selection_date"
        )
    )

    if current_date_state != selected_date:

        # For now every detected Polaroid is Pending,
        # so preselect all Pending Polaroids.
        st.session_state[
            "polaroid_selected_ids"
        ] = {
            get_polaroid_id(polaroid)
            for polaroid in date_polaroids
        }

        st.session_state[
            "polaroid_selection_date"
        ] = selected_date

        st.session_state.pop(
            "polaroid_batch_zip",
            None
        )

    selected_ids = set(
        st.session_state.get(
            "polaroid_selected_ids",
            set()
        )
    )

    selected_count = len([
        polaroid
        for polaroid in date_polaroids
        if get_polaroid_id(polaroid) in selected_ids
    ])

    # ---------------- BULK CONTROLS ----------------



    bulk_col_1, bulk_col_2, bulk_col_3 = (
        st.columns([1.4, 1, 4])
    )

    with bulk_col_1:
        if st.button(
            "✓ Select All Pending",
            use_container_width=True,
            key="select_all_pending"
        ):
            st.session_state[
                "polaroid_selected_ids"
            ] = {
                get_polaroid_id(
                    polaroid
                )
                for polaroid
                in date_polaroids
            }

            st.session_state.pop(
                "polaroid_batch_zip",
                None
            )

            st.rerun()

    with bulk_col_2:
        if st.button(
            "Clear Selection",
            use_container_width=True,
            key="clear_polaroid_selection"
        ):
            st.session_state[
                "polaroid_selected_ids"
            ] = set()

            st.session_state.pop(
                "polaroid_batch_zip",
                None
            )

            st.rerun()

    # with bulk_col_3:
    #    st.markdown(
    #        f"**{selected_count} selected**"
    #    ) 


    # ---------------- SELECTABLE TABLE ----------------

    table_rows = []

    for polaroid in date_polaroids:
        polaroid_id = get_polaroid_id(
            polaroid
        )

        order_number = polaroid.get("order")

        detrack_status = (
            "UPLOADED"
            if order_number in existing_detrack_orders
            else "PENDING"
        )

        table_rows.append({
            "Select": (
                polaroid_id
                in selected_ids
            ),

            detrack_status = (
                "UPLOADED"
                if order_number in existing_detrack_orders
                else "PENDING"
            ),

            # Placeholder until persistent
            # download history is added.
            "Purchased At": format_purchase_time(
                polaroid.get("purchased_at")
            ),

            "Order": polaroid.get(
                "order"
            ),

            "Recipient": polaroid.get(
                "recipient"
            ),

            "Slot": polaroid.get(
                "delivery_slot"
            ),

            "Status": "Pending",

            # Hidden working ID.
            "_polaroid_id": polaroid_id,
        })

    edited_rows = st.data_editor(
        table_rows,
        use_container_width=True,
        hide_index=True,
        key=(
            f"polaroid_editor_"
            f"{selected_date}"
        ),
        disabled=[
            "Detrack Status",
            "Order",
            "Recipient",
            "Slot",
            "Status",
            "_polaroid_id",
        ],
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help=(
                    "Include this Polaroid "
                    "in the next ZIP."
                ),
                default=False,
            ),

            "Last Downloaded": (
                st.column_config.TextColumn(
                    "Last Downloaded"
                )
            ),

            "Order": (
                st.column_config.TextColumn(
                    "Order"
                )
            ),

            "Recipient": (
                st.column_config.TextColumn(
                    "Recipient"
                )
            ),

            "Slot": (
                st.column_config.TextColumn(
                    "Slot"
                )
            ),

            "Status": (
                st.column_config.TextColumn(
                    "Status"
                )
            ),

            "_polaroid_id": None,
        }
    )

    # ---------------- READ CHECKBOX CHANGES ----------------

    new_selected_ids = {
        row["_polaroid_id"]
        for row in edited_rows
        if row.get("Select")
    }

    if new_selected_ids != selected_ids:
        st.session_state[
            "polaroid_selected_ids"
        ] = new_selected_ids

        st.session_state.pop(
            "polaroid_batch_zip",
            None
        )

        selected_ids = (
            new_selected_ids
        )

    selected_polaroids = [
        polaroid
        for polaroid in date_polaroids
        if get_polaroid_id(
            polaroid
        ) in selected_ids
    ]

    selected_count = len(
        selected_polaroids
    )

    # ---------------- DOWNLOAD AREA ----------------

    st.divider()

    st.markdown(
        f"## {selected_count} "
        f"Polaroid"
        f"{'s' if selected_count != 1 else ''} "
        f"Selected"
    )

    st.caption(
        "Only selected rows will be included "
        "in this ZIP."
    )

    if st.button(
        (
            f"Prepare {selected_count} "
            f"Polaroid"
            f"{'s' if selected_count != 1 else ''}"
        ),
        type="primary",
        disabled=(selected_count == 0),
        key="prepare_selected_polaroids"
    ):
        with st.spinner(
            f"Preparing "
            f"{selected_count} Polaroids..."
        ):
            try:
                batch_result = (
                    prepare_selected_polaroids(
                        selected_polaroids,
                        selected_date
                    )
                )

                st.session_state[
                    "polaroid_batch_zip"
                ] = batch_result

            except Exception as e:
                st.error(
                    f"Could not prepare batch: {e}"
                )

    batch_result = st.session_state.get(
        "polaroid_batch_zip"
    )

    if (
        batch_result
        and batch_result.get(
            "delivery_date"
        ) == selected_date
    ):
        successful = batch_result.get(
            "successful",
            []
        )

        failed = batch_result.get(
            "failed",
            []
        )

        successful_count = len(
            successful
        )

        failed_count = len(
            failed
        )

        if successful_count:
            st.success(
                f"{successful_count} files "
                f"ready for download."
            )

        if failed_count:
            st.error(
                f"{failed_count} Polaroid"
                f"{'s' if failed_count != 1 else ''} "
                f"could not be downloaded. "
                f"Do not treat this as "
                f"a complete batch."
            )

            with st.expander(
                "View failed Polaroids"
            ):
                st.dataframe(
                    failed,
                    use_container_width=True,
                    hide_index=True
                )

        with st.expander(
            "Files included in ZIP"
        ):
            st.dataframe(
                successful,
                use_container_width=True,
                hide_index=True
            )

        st.download_button(
                label=(
                    f"Download "
                    f"{successful_count} "
                    f"Polaroid"
                    f"{'s' if successful_count != 1 else ''}"
                ),
                data=batch_result["bytes"],
                file_name=(
                    batch_result[
                        "filename"
                    ]
                ),
                mime="application/zip",
                type="primary",
                key="download_polaroid_zip"
            )    


# ----------------------- POLAROID TESTING -----------------------

def display_polaroid_test():
    st.subheader("Polaroid Upload Test")

    test_order = st.text_input(
        "Enter Shopify order number",
        placeholder="#TDBXXXXX"
    )

    if not test_order:
        st.info(
            "Enter an order number containing "
            "a Polaroid upload."
        )
        return

    orders = get_orders()

    matched_order = None

    for order in orders:
        if order.get("name") == test_order:
            matched_order = order
            break

    if not matched_order:
        st.error(
            f"Order {test_order} not found."
        )
        return

    st.success(
        f"Found {matched_order.get('name')}"
    )

    line_items = matched_order.get(
        "line_items",
        []
    )

    if not line_items:
        st.warning(
            "No line items found for this order."
        )
        return

    # ---------------- REST ORDER DATA ----------------

    st.subheader("REST API Comparison")

    for item in line_items:
        st.divider()

        item_title = item.get("title")
        sku = item.get("sku")
        line_item_id = item.get("id")

        properties = item.get(
            "properties",
            []
        )

        bundle_key = None
        photo_url = None

        for prop in properties:
            name = prop.get("name")
            value = prop.get("value")

            if name == "_gs_bundle_key":
                bundle_key = value

            if name == "Photo Upload":
                photo_url = value

        st.write(
            "**Item:**",
            item_title
        )

        st.write(
            "**SKU:**",
            sku
        )

        st.write(
            "**Line Item ID:**",
            line_item_id
        )

        with st.expander(
            "Raw Line Item JSON"
        ):
            st.json(item)

        st.write("**Bundle Key:**")

        if bundle_key:
            st.code(bundle_key)
        else:
            st.write("None")

        st.write(
            "**Raw Photo Upload Value:**"
        )

        if photo_url:
            st.code(
                repr(photo_url)
            )

            if photo_url.startswith(
                ("http://", "https://")
            ):
                st.success(
                    "Full URL received from "
                    "Shopify REST API"
                )

                st.link_button(
                    "Open Uploaded Photo",
                    photo_url
                )

            else:
                st.warning(
                    "Shopify REST API returned "
                    "a filename/path rather than "
                    "a full URL."
                )

        else:
            st.write("None")

        st.write(
            "**All Properties:**"
        )

        if not properties:
            st.write(
                "No line item properties found."
            )

        else:
            for prop in properties:
                st.write(prop)

    # ---------------- GRAPHQL ORDER DATA ----------------

    st.divider()

    st.subheader(
        "GraphQL Bundle Line Properties"
    )

    shopify_order_id = (
        matched_order.get("id")
    )

    try:
        graphql_order = (
            get_order_graphql(
                shopify_order_id
            )
        )

        if not graphql_order:
            st.warning(
                "GraphQL order was not found."
            )
            return

        st.write(
            "**GraphQL Order:**",
            graphql_order.get("name")
        )

        graphql_line_items = (
            graphql_order
            .get("lineItems", {})
            .get("nodes", [])
        )

        if not graphql_line_items:
            st.warning(
                "No GraphQL line items found."
            )
            return

        for item in graphql_line_items:
            st.divider()

            item_title = item.get(
                "title"
            )

            item_name = item.get(
                "name"
            )

            sku = item.get(
                "sku"
            )

            line_item_id = item.get(
                "id"
            )

            line_item_group = (
                item.get(
                    "lineItemGroup"
                )
            )

            st.write(
                "**Item:**",
                item_title or item_name
            )

            st.write(
                "**SKU:**",
                sku
            )

            st.write(
                "**GraphQL Line Item ID:**",
                line_item_id
            )

            if not line_item_group:
                st.write(
                    "**Line Item Group:** None"
                )
                continue

            group_id = (
                line_item_group.get(
                    "id"
                )
            )

            group_title = (
                line_item_group.get(
                    "title"
                )
            )

            group_quantity = (
                line_item_group.get(
                    "quantity"
                )
            )

            attributes = (
                line_item_group.get(
                    "customAttributes",
                    []
                )
            )

            st.write(
                "**Bundle Group ID:**"
            )
            st.code(group_id)

            st.write(
                "**Bundle Group Title:**"
            )
            st.write(group_title)

            st.write(
                "**Bundle Group Quantity:**"
            )
            st.write(group_quantity)

            graphql_photo_value = None

            for attribute in attributes:
                key = attribute.get(
                    "key"
                )

                value = attribute.get(
                    "value"
                )

                if key == "Photo Upload":
                    graphql_photo_value = (
                        value
                    )
                    break

            st.write(
                "**Bundle Photo Upload Value:**"
            )

            if graphql_photo_value:
                st.code(
                    repr(
                        graphql_photo_value
                    )
                )

                if graphql_photo_value.startswith(
                    ("http://", "https://")
                ):
                    st.success(
                        "Bundle Line Properties "
                        "returned a full photo URL."
                    )

                    st.link_button(
                        "Open Bundle Uploaded Photo",
                        graphql_photo_value,
                        key=(
                            f"bundle_photo_"
                            f"{line_item_id}"
                        )
                    )

                else:
                    st.warning(
                        "Bundle Line Properties "
                        "returned a filename/path "
                        "rather than a full URL."
                    )

            else:
                st.write("None")

            st.write(
                "**All Bundle Line Properties:**"
            )

            if not attributes:
                st.write(
                    "No bundle line "
                    "properties found."
                )

            else:
                for attribute in attributes:
                    st.write(
                        attribute
                    )

    except Exception as e:
        st.error(
            f"GraphQL test failed: {e}"
        )

    # ---------------- QUEUE TEST ----------------

    st.divider()

    st.subheader(
        "Polaroid Queue Test"
    )

    if st.button(
        "Build Polaroid Queue"
    ):
        with st.spinner(
            "Building Polaroid queue..."
        ):
            st.session_state[
                "polaroid_queue"
            ] = build_polaroid_queue()

    queue = st.session_state.get(
        "polaroid_queue",
        []
    )

    if queue:
        st.write(
            f"**Polaroids detected:** "
            f"{len(queue)}"
        )

        st.dataframe(
            queue,
            use_container_width=True
        )

        st.divider()

        st.subheader(
            "Single Polaroid Download Test"
        )

        st.caption(
            "Downloads one Polaroid only. "
            "This does not update any "
            "print status."
        )

        options = {}

        for index, polaroid in enumerate(
            queue
        ):
            order_name = (
                polaroid.get("order")
            )

            recipient = (
                polaroid.get("recipient")
            )

            source = (
                polaroid.get("source")
            )

            delivery_date = (
                polaroid.get(
                    "delivery_date"
                )
            )

            label = (
                f"{order_name} | "
                f"{recipient} | "
                f"{delivery_date} | "
                f"{source}"
            )

            options[
                f"{index} - {label}"
            ] = polaroid

        selected_label = st.selectbox(
            "Select one Polaroid to test",
            options=list(
                options.keys()
            )
        )

        selected_polaroid = (
            options[selected_label]
        )

        photo_url = (
            selected_polaroid.get(
                "photo_url"
            )
        )

        order_name = (
            selected_polaroid.get(
                "order",
                "polaroid"
            )
        )

        source = (
            selected_polaroid.get(
                "source",
                ""
            )
        )

        st.write(
            "**Selected URL:**"
        )

        st.code(photo_url)

        if st.button(
            "Fetch Selected Polaroid"
        ):
            try:
                (
                    image_bytes,
                    content_type,
                    extension
                ) = fetch_polaroid_image(
                    photo_url
                )

                st.session_state[
                    "test_polaroid_bytes"
                ] = image_bytes

                st.session_state[
                    "test_polaroid_content_type"
                ] = content_type

                st.session_state[
                    "test_polaroid_extension"
                ] = extension

                st.session_state[
                    "test_polaroid_order"
                ] = order_name

                st.session_state[
                    "test_polaroid_source"
                ] = source

                st.success(
                    "Polaroid fetched "
                    "successfully."
                )

            except Exception as e:
                st.error(
                    f"Could not fetch "
                    f"Polaroid: {e}"
                )

        image_bytes = (
            st.session_state.get(
                "test_polaroid_bytes"
            )
        )

        if image_bytes:
            test_order_name = (
                st.session_state.get(
                    "test_polaroid_order",
                    "polaroid"
                )
            )

            test_source = (
                st.session_state.get(
                    "test_polaroid_source",
                    ""
                )
            )

            content_type = (
                st.session_state.get(
                    "test_polaroid_content_type",
                    "image/jpeg"
                )
            )

            extension = (
                st.session_state.get(
                    "test_polaroid_extension",
                    "jpg"
                )
            )

            clean_order = (
                clean_filename_part(
                    test_order_name
                )
            )

            clean_source = (
                clean_filename_part(
                    test_source
                )
            )

            filename = (
                f"{clean_order}_"
                f"{clean_source}_"
                f"TEST."
                f"{extension}"
            )

            st.write(
                f"**Image size:** "
                f"{len(image_bytes):,} bytes"
            )

            st.write(
                "**Content Type:**",
                content_type
            )

            st.image(
                image_bytes,
                caption=(
                    f"{test_order_name} — "
                    f"{test_source}"
                ),
                width=300
            )

            st.download_button(
                label=(
                    "Download Test Polaroid"
                ),
                data=image_bytes,
                file_name=filename,
                mime=content_type
            )

    elif (
        "polaroid_queue"
        in st.session_state
    ):
        st.warning(
            "No Polaroids detected."
        )


# ----------------------- DASHBOARD -----------------------

# Displays login page to authenticate users
if not check_password():
    st.stop()


# Set browser tab
st.set_page_config(
    page_title=(
        "The Daily Blooms Dashboard"
    ),
    page_icon="assets/flower_logo.png",
    layout="wide"
)


# Dashboard header
header_col, refresh_col = (
    st.columns([8, 1])
)

with header_col:
    st.header(
        "The Daily Blooms Dashboard"
    )

with refresh_col:
    if st.button(
        "Refresh",
        use_container_width=True
    ):
        st.rerun()


# Main dashboard sections
(
    orders_tab,
    detrack_tab,
    polaroid_tab
) = st.tabs([
    "Orders",
    "Detrack Sync",
    "Polaroid Printing"
])


with orders_tab:
    filtered_table_data = (
        display_order_details_table()
    )

    display_order_summary_tables(
        filtered_table_data
    )


with detrack_tab:
    display_detrack_sync()


with polaroid_tab:
    display_polaroid_printing()



# Insert empty space to optimise UI
st.markdown(
    "<br>",
    unsafe_allow_html=True
)