from shopify_client import get_orders, get_order_graphql
from order_processor import (
    get_delivery_date,
    get_delivery_slot,
    standardise_date,
)


PHOTO_UPLOAD_KEY = "Photo Upload"


def attributes_to_dict(attributes):
    """
    Convert Shopify GraphQL customAttributes into
    a normal Python dictionary.
    """
    return {
        attribute.get("key"): attribute.get("value")
        for attribute in attributes or []
        if attribute.get("key")
    }


def properties_to_dict(properties):
    """
    Convert Shopify REST line item properties into
    a normal Python dictionary.
    """
    return {
        prop.get("name"): prop.get("value")
        for prop in properties or []
        if prop.get("name")
    }


def get_numeric_line_item_id(graphql_id):
    """
    Converts:
    gid://shopify/LineItem/15064782241838

    into:
    15064782241838
    """
    if not graphql_id:
        return None

    return str(graphql_id).split("/")[-1]


def is_full_url(value):
    if not value:
        return False

    return str(value).startswith(
        ("http://", "https://")
    )


def find_order_delivery_date(order):
    """
    Fallback delivery date for an order.

    Uses the existing delivery-date logic in
    order_processor.py.
    """
    for item in order.get("line_items", []):
        date = get_delivery_date(order, item)

        if date:
            return standardise_date(date)

    return None


def find_order_delivery_slot(order):
    """
    Fallback delivery slot for an order.
    """
    for item in order.get("line_items", []):
        slot = get_delivery_slot(order, item)

        if slot:
            return slot

    return None


def find_attribute_delivery_date(attributes):
    """
    Attempts to retrieve Delivery Date directly
    from GraphQL custom attributes.
    """
    value = attributes.get("Delivery Date")

    if not value:
        return None

    return standardise_date(value)


def find_attribute_delivery_slot(attributes):
    """
    Giftship uses different property names depending
    on weekday/weekend/seasonal configuration.
    """
    possible_keys = [
        "Delivery Timeslot Weekday",
        "Delivery Timeslot Weekend",
        "Delivery Timeslot Seasonal",
        "Pickup Timeslot Weekday",
        "Pickup Timeslot Weekend",
    ]

    for key in possible_keys:
        value = attributes.get(key)

        if value:
            return value

    return None


def has_possible_polaroid(order):
    """
    Cheap REST check before making a GraphQL request.

    This prevents us from calling GraphQL for every
    Shopify order when the order clearly contains
    no Polaroid.
    """
    for item in order.get("line_items", []):
        sku = str(item.get("sku") or "").lower()

        properties = properties_to_dict(
            item.get("properties", [])
        )

        # Direct Photo Upload property
        if properties.get(PHOTO_UPLOAD_KEY):
            return True

        # Separate Polaroid add-on
        if sku == "polaroid":
            return True

        # Polaroid encoded into a combined SKU
        if "polaroid" in sku:
            return True

    return False


def build_rest_line_item_map(order):
    """
    Build REST line-item lookup by Shopify line item ID.
    """
    return {
        str(item.get("id")): item
        for item in order.get("line_items", [])
        if item.get("id")
    }


def get_recipient(order):
    shipping_address = order.get("shipping_address") or {}

    return (
        shipping_address.get("name")
        or shipping_address.get("first_name")
        or ""
    )


def build_polaroid_queue():
    """
    Build one normalised queue containing both:

    1. Direct / main-product Photo Uploads
    2. Giftship bundled Photo Uploads

    One returned row represents one unique uploaded photo.
    """

    orders = get_orders()

    queue = []

    # Used to stop one Giftship bundle appearing multiple
    # times because multiple line items can share a group.
    seen_photos = set()

    for order in orders:

        # Avoid unnecessary GraphQL calls
        if not has_possible_polaroid(order):
            continue

        try:
            graphql_order = get_order_graphql(order["id"])
        except Exception as e:
            queue.append({
                "shopify_id": order.get("id"),
                "order": order.get("name"),
                "recipient": get_recipient(order),
                "delivery_date": find_order_delivery_date(order),
                "delivery_slot": find_order_delivery_slot(order),
                "line_item_id": None,
                "bundle_group_id": None,
                "source": "ERROR",
                "photo_url": None,
                "photo_value": None,
                "downloadable": False,
                "status": "Error",
                "error": str(e),
            })

            continue

        graphql_line_items = (
            graphql_order
            .get("lineItems", {})
            .get("nodes", [])
        )

        rest_line_items = build_rest_line_item_map(order)

        for graphql_item in graphql_line_items:
            graphql_line_item_id = graphql_item.get("id")

            numeric_line_item_id = get_numeric_line_item_id(
                graphql_line_item_id
            )

            rest_item = rest_line_items.get(
                numeric_line_item_id,
                {}
            )

            rest_properties = properties_to_dict(
                rest_item.get("properties", [])
            )

            direct_attributes = attributes_to_dict(
                graphql_item.get("customAttributes", [])
            )

            line_item_group = (
                graphql_item.get("lineItemGroup")
                or {}
            )

            bundle_attributes = attributes_to_dict(
                line_item_group.get("customAttributes", [])
            )

            # -------------------------------------------------
            # TYPE 1:
            # Giftship bundle Photo Upload
            # -------------------------------------------------

            bundle_photo = bundle_attributes.get(
                PHOTO_UPLOAD_KEY
            )

            if bundle_photo:
                bundle_group_id = line_item_group.get("id")

                # Multiple line items may point to the same group,
                # so deduplicate using the group + photo.
                unique_key = (
                    str(order.get("id")),
                    str(bundle_group_id),
                    str(bundle_photo),
                )

                if unique_key not in seen_photos:
                    seen_photos.add(unique_key)

                    delivery_date = (
                        find_attribute_delivery_date(
                            bundle_attributes
                        )
                        or find_order_delivery_date(order)
                    )

                    delivery_slot = (
                        find_attribute_delivery_slot(
                            bundle_attributes
                        )
                        or find_order_delivery_slot(order)
                    )

                    queue.append({
                        "shopify_id": order.get("id"),
                        "order": order.get("name"),
                        "recipient": get_recipient(order),
                        "delivery_date": delivery_date,
                        "delivery_slot": delivery_slot,
                        "line_item_id": numeric_line_item_id,
                        "bundle_group_id": bundle_group_id,
                        "source": "Bundle",
                        "photo_url": (
                            bundle_photo
                            if is_full_url(bundle_photo)
                            else None
                        ),
                        "photo_value": bundle_photo,
                        "downloadable": is_full_url(
                            bundle_photo
                        ),
                        "status": "Pending",
                        "error": None,
                    })

            # -------------------------------------------------
            # TYPE 2:
            # Direct / main-product Photo Upload
            # -------------------------------------------------

            direct_photo = direct_attributes.get(
                PHOTO_UPLOAD_KEY
            )

            rest_photo = rest_properties.get(
                PHOTO_UPLOAD_KEY
            )

            # Prefer GraphQL value first.
            # Fall back to REST if necessary.
            direct_photo_value = (
                direct_photo
                or rest_photo
            )

            if direct_photo_value:
                unique_key = (
                    str(order.get("id")),
                    str(numeric_line_item_id),
                    str(direct_photo_value),
                )

                if unique_key not in seen_photos:
                    seen_photos.add(unique_key)

                    delivery_date = (
                        find_attribute_delivery_date(
                            direct_attributes
                        )
                        or standardise_date(
                            get_delivery_date(
                                order,
                                rest_item
                            )
                        )
                        or find_order_delivery_date(order)
                    )

                    delivery_slot = (
                        find_attribute_delivery_slot(
                            direct_attributes
                        )
                        or (
                            get_delivery_slot(
                                order,
                                rest_item
                            )
                            if rest_item
                            else None
                        )
                        or find_order_delivery_slot(order)
                    )

                    queue.append({
                        "shopify_id": order.get("id"),
                        "order": order.get("name"),
                        "recipient": get_recipient(order),
                        "delivery_date": delivery_date,
                        "delivery_slot": delivery_slot,
                        "line_item_id": numeric_line_item_id,
                        "bundle_group_id": None,
                        "source": "Direct",
                        "photo_url": (
                            direct_photo_value
                            if is_full_url(
                                direct_photo_value
                            )
                            else None
                        ),
                        "photo_value": direct_photo_value,
                        "downloadable": is_full_url(
                            direct_photo_value
                        ),
                        "status": "Pending",
                        "error": None,
                    })

    return queue