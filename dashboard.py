import streamlit as st

from components.authentication import check_password
from components.order_details_table import display_order_details_table
from components.order_summary_tables import display_order_summary_tables
from components.detrack_sync import display_detrack_sync

from shopify_client import get_orders, get_order_graphql

from detrack.order_builder import build_delivery_orders
from detrack.sku_mapping import get_sku_tag_mapping
from detrack.tag_calculator import calculate_tags
from detrack.validator import validate_order


# ----------------------- TESTING CODE -----------------------

def display_polaroid_test():
    st.subheader("Polaroid Upload Test")

    test_order = st.text_input(
        "Enter Shopify order number",
        placeholder="#TDBXXXXX"
    )

    if not test_order:
        st.info("Enter an order number containing a Polaroid upload.")
        return

    orders = get_orders()

    matched_order = None

    for order in orders:
        if order.get("name") == test_order:
            matched_order = order
            break

    if not matched_order:
        st.error(f"Order {test_order} not found.")
        return

    st.success(f"Found {matched_order.get('name')}")

    line_items = matched_order.get("line_items", [])

    if not line_items:
        st.warning("No line items found for this order.")
        return

    # ---------------- REST ORDER DATA ----------------

    st.subheader("REST API Comparison")

    for item in line_items:
        st.divider()

        item_title = item.get("title")
        sku = item.get("sku")
        line_item_id = item.get("id")
        properties = item.get("properties", [])

        bundle_key = None
        photo_url = None

        # Extract key Giftship properties
        for prop in properties:
            name = prop.get("name")
            value = prop.get("value")

            if name == "_gs_bundle_key":
                bundle_key = value

            if name == "Photo Upload":
                photo_url = value

        st.write("**Item:**", item_title)
        st.write("**SKU:**", sku)
        st.write("**Line Item ID:**", line_item_id)

        with st.expander("Raw Line Item JSON"):
            st.json(item)

        st.write("**Bundle Key:**")

        if bundle_key:
            st.code(bundle_key)
        else:
            st.write("None")

        st.write("**Raw Photo Upload Value:**")

        if photo_url:
            st.code(repr(photo_url))

            if photo_url.startswith(("http://", "https://")):
                st.success("Full URL received from Shopify REST API")

                st.link_button(
                    "Open Uploaded Photo",
                    photo_url
                )
            else:
                st.warning(
                    "Shopify REST API returned a filename/path "
                    "rather than a full URL."
                )
        else:
            st.write("None")

        st.write("**All Properties:**")

        if not properties:
            st.write("No line item properties found.")
        else:
            for prop in properties:
                st.write(prop)

    # ---------------- GRAPHQL ORDER DATA ----------------

    st.divider()
    st.subheader("GraphQL Bundle Line Properties")

    shopify_order_id = matched_order.get("id")

    try:
        graphql_order = get_order_graphql(shopify_order_id)

        if not graphql_order:
            st.warning("GraphQL order was not found.")
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
            st.warning("No GraphQL line items found.")
            return

        for item in graphql_line_items:
            st.divider()

            item_title = item.get("title")
            item_name = item.get("name")
            sku = item.get("sku")
            line_item_id = item.get("id")
            line_item_group = item.get("lineItemGroup")

            st.write("**Item:**", item_title or item_name)
            st.write("**SKU:**", sku)
            st.write("**GraphQL Line Item ID:**", line_item_id)

            # This line item is not part of a Shopify line item group
            if not line_item_group:
                st.write("**Line Item Group:** None")
                continue

            group_id = line_item_group.get("id")
            group_title = line_item_group.get("title")
            group_quantity = line_item_group.get("quantity")
            attributes = line_item_group.get("customAttributes", [])

            st.write("**Bundle Group ID:**")
            st.code(group_id)

            st.write("**Bundle Group Title:**")
            st.write(group_title)

            st.write("**Bundle Group Quantity:**")
            st.write(group_quantity)

            graphql_photo_value = None

            for attribute in attributes:
                key = attribute.get("key")
                value = attribute.get("value")

                if key == "Photo Upload":
                    graphql_photo_value = value
                    break

            st.write("**Bundle Photo Upload Value:**")

            if graphql_photo_value:
                st.code(repr(graphql_photo_value))

                if graphql_photo_value.startswith(
                    ("http://", "https://")
                ):
                    st.success(
                        "Bundle Line Properties returned a full photo URL."
                    )

                    st.link_button(
                        "Open Bundle Uploaded Photo",
                        graphql_photo_value,
                        key=f"bundle_photo_{line_item_id}"
                    )
                else:
                    st.warning(
                        "Bundle Line Properties returned a filename/path "
                        "rather than a full URL."
                    )
            else:
                st.write("None")

            st.write("**All Bundle Line Properties:**")

            if not attributes:
                st.write("No bundle line properties found.")
            else:
                for attribute in attributes:
                    st.write(attribute)

    except Exception as e:
        st.error(f"GraphQL test failed: {e}")


# ----------------------- ORIGINAL CODE BELOW -----------------------

# Displays login page to authenticate users
if not check_password():
    st.stop()

# Set browser tab
st.set_page_config(
    page_title="The Daily Blooms Dashboard",
    page_icon="assets/flower_logo.png",
    layout="wide"
)

# Dashboard header with refresh button on the right
header_col, refresh_col = st.columns([8, 1])

with header_col:
    st.header("The Daily Blooms Dashboard")

with refresh_col:
    if st.button("Refresh", use_container_width=True):
        st.rerun()

# Main dashboard sections
orders_tab, detrack_tab, polaroid_test_tab = st.tabs([
    "Orders",
    "Detrack Sync",
    "Polaroid Test"
])

with orders_tab:
    # Order details table
    filtered_table_data = display_order_details_table()

    # Summary tables
    display_order_summary_tables(filtered_table_data)

with detrack_tab:
    display_detrack_sync()

with polaroid_test_tab:
    display_polaroid_test()

# Enables refresh
# Upon refresh, the date and timeslots will return to
# default state of the earliest date and all timeslots respectively.
#
# if st.button("Refresh"):
#     st.session_state.selected_date = None
#     st.session_state.selected_slots = []
#     st.rerun()

# Insert empty space to optimise UI
st.markdown("<br>", unsafe_allow_html=True)