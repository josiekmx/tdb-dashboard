from datetime import datetime


# Validate one order before it can be uploaded to Detrack
def validate_order(delivery_order, missing_skus):
    errors = []
    warnings = []

    # Delivery type must be valid
    if delivery_order.delivery_type not in ["Delivery", "Pickup"]:
        errors.append("Missing or invalid delivery type")

    # Delivery / pickup date must exist and be valid
    if not delivery_order.delivery_date:
        errors.append("Missing delivery date")
    else:
        try:
            datetime.strptime(
                delivery_order.delivery_date,
                "%Y-%m-%d"
            )
        except ValueError:
            errors.append("Invalid delivery date")

    # Timeslot is required
    if not delivery_order.delivery_slot:
        errors.append("Missing timeslot")

    # Recipient details are warnings only
    if not delivery_order.recipient_name:
        warnings.append("Missing recipient name")

    if not delivery_order.recipient_phone:
        warnings.append("Missing recipient phone")

    # Address and postal code are compulsory for deliveries only
    if delivery_order.delivery_type == "Delivery":
        if not delivery_order.address:
            errors.append("Missing delivery address")

        if not delivery_order.postal_code:
            errors.append("Missing postal code")

    # Missing SKU mapping is a warning and does not block upload
    if missing_skus:
        warnings.append(
            "Missing SKU tag mapping: " + ", ".join(missing_skus)
        )

    # Determine final validation status
    if errors:
        delivery_order.validation_status = "ERROR"
        delivery_order.validation_messages = errors + warnings

    elif warnings:
        delivery_order.validation_status = "WARNING"
        delivery_order.validation_messages = warnings

    else:
        delivery_order.validation_status = "READY"
        delivery_order.validation_messages = []

    return delivery_order