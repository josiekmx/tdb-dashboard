# Calculate total number of tags required for one order
def calculate_tags(delivery_order, sku_mapping):
    total_tags = 0
    missing_skus = []

    for item in delivery_order.line_items:
        sku = str(item.sku).strip().upper()

        # Custom products without a SKU default to 1 tag each
        if sku == "NO SKU - CHECK CUSTOM ORDER":
            total_tags += item.quantity
            continue

        if sku not in sku_mapping:
            missing_skus.append(sku)
            continue

        tags_per_item = sku_mapping[sku]
        total_tags += tags_per_item * item.quantity

    return total_tags, missing_skus