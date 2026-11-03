
from procurement.sheets_client import get_flower_recipe_rows


def get_recipe_library():
    """
    Read all SKUs and their flower recipes.

    Keeps SKUs with empty recipes.
    Does not modify Google Sheets.
    """

    rows = get_flower_recipe_rows()

    if not rows:
        return {}

    headers = rows[0]
    flower_names = headers[1:]

    library = {}

    for row_number, row in enumerate(rows[1:], start=2):
        if not row:
            continue

        sku = str(row[0]).strip()

        if not sku:
            continue

        # Preserve SKU spelling for display.
        # Normalize case only for matching.
        sku_key = sku.upper()

        flowers = {}
        issues = []

        for index, flower_name in enumerate(
            flower_names, start=1
        ):
            flower_name = str(flower_name).strip()

            if not flower_name:
                continue

            value = row[index] if index < len(row) else ""
            value = str(value).strip()

            if not value:
                continue

            try:
                quantity = float(value)

                if quantity < 0:
                    issues.append(
                        f"Negative quantity: {flower_name}"
                    )
                elif quantity > 0:
                    flowers[flower_name] = quantity

            except ValueError:
                issues.append(
                    f"Invalid quantity: {flower_name} = {value}"
                )

        recipe = {
            "sku": sku,
            "flowers": flowers,
            "has_recipe": bool(flowers),
            "issues": issues,
            "sheet_row": row_number,
        }

        # Preserve duplicates for review rather than
        # silently overwriting the existing SKU.
        library.setdefault(sku_key, []).append(recipe)

    return library


def lookup_recipe(sku):
    """
    Look up one SKU from the Flower Recipe sheet.
    """

    sku_key = str(sku).strip().upper()

    if not sku_key:
        return {
            "status": "empty_search",
            "matches": [],
        }

    library = get_recipe_library()
    matches = library.get(sku_key, [])

    if not matches:
        status = "not_found"
    elif len(matches) > 1:
        status = "duplicate"
    elif matches[0]["issues"]:
        status = "invalid"
    elif not matches[0]["has_recipe"]:
        status = "no_recipe"
    else:
        status = "found"

    return {
        "status": status,
        "matches": matches,
    }
