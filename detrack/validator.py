from datetime import datetime


# Validate one order before it can be uploaded to Detrack
def validate_order(delivery_order, missing_skus):
    errors = []
    warnings = []

    # Validate delivery / pickup type
    if delivery_order.delivery_type not in ["Delivery", "Pickup"]:
        errors.append("Missing or invalid delivery type")

    # Validate date
    if not delivery_order.delivery_date:
        errors.append("Missing delivery date")
    else:
        try:
            datetime.strptime(delivery_order.delivery_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid delivery date")

    # Validate timeslot
    if not delivery_order.delivery_slot:
        errors.append("Missing timeslot")

    # Validate recipient details
    if not delivery_order.recipient_name:
        errors.append("Missing recipient name")

    if not delivery_order.recipient_phone:
        errors.append("Missing recipient phone")

    # Address is required for delivery but not pickup
    if delivery_order.delivery_type == "Delivery":
        if not delivery_order.address:
            errors.append("Missing delivery address")

        if not delivery_order.postal_code:
            errors.append("Missing postal code")

    # Every SKU must have a tag mapping
    if missing_skus:
        warnings.append(
            "Missing SKU tag mapping: " + ", ".join(missing_skus)
    )

    # Determine final validation status
    if errors:
        order.validation_status = "ERROR"
        order.validation_messages = errors + warnings

    elif warnings:
        order.validation_status = "WARNING"
        order.validation_messages = warnings

    else:
        order.validation_status = "READY"
        order.validation_messages = []

    return order


    delivery_order.validation_status = status
    delivery_order.validation_messages = errors + warnings

    return delivery_order