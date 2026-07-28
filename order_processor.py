import pandas as pd
from shopify_client import get_orders
import re
from datetime import datetime
import json
import os 
import streamlit as st
from components.completion_store import cleanup_completed_orders

# definining add-on products
MUSIC_BOX_SKUS = {
    "Music-HDB",
    "Music-AWM",
    "Music-OTR",
    "Music-BB",
}
SCENT_SKUS = {
    "LAV50",
    "FRE50",
    "ROS50",
    "LIL50",
    "MAG50",
}

# helper functions
def is_ribbon(sku):
    return sku == "Ribbon"

def is_music_box(sku):
    return sku in MUSIC_BOX_SKUS

def is_polaroid(sku):
    return sku == "Polaroid"

def is_scent(sku):
    return sku in SCENT_SKUS

def get_delivery_date(order, item):
    # loop through properties and return 
    # delivery date if this property is available
    for prop in item.get("properties", []):
        if prop["name"] == "Delivery Date":
            # in cases of a date change
            # search for delivery date within given tags
             if "datechange" in order["tags"].lower() or "date change" in order["tags"].lower() :
                 match = re.search(r"\d{4}-\d{2}-\d{2}", order["tags"])
                 if match:
                    return match.group()
             return prop["value"]

    # if no delivery date property is available,
    # search for delivery date within given tags
    match = re.search(r"\d{4}-\d{2}-\d{2}", order["tags"])
    if match:
        return match.group()
    return None

# standardise dates to "%Y-%m-%d" format
def standardise_date(date_str):
    if not date_str:
        return None

    # possible data formats in raw data
    formats = [
        "%Y-%m-%d",   # 2026-07-30
        "%d/%m/%Y",   # 25/6/2026
    ]

    for fmt in formats:
        try:
            date = datetime.strptime(date_str, fmt)
            return date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def get_delivery_slot(order, item):
    # search for delivery or pickup timeslot within given tags
    if "9:00 AM - 2:00 PM" in order["tags"]:
        return "9:00 AM - 2:00 PM"
    elif "1:00 PM - 6:00 PM" in order["tags"]:
        return "1:00 PM - 6:00 PM"
    elif "5:00 PM - 10:00 PM" in order["tags"]:
        return "5:00 PM - 10:00 PM"
    elif "pickup" in order["tags"].lower() or  "pick up" in order["tags"].lower():
        return "Pick up"
    else:
        # irregular category
        return "Custom Time"

# updates addon item information accurately with
# understanding of the sku name
# eg. F-Ribbon-Polaroid-FRE50 -> ribbon, polaroid, scent is updated to True
def update_addons_using_sku(sku, ribbon, music_box, polaroid, scent):
    lowercase_sku = str(sku).lower()
    updated_addon_list = [ribbon, music_box.copy(), polaroid, scent.copy()]
    if "ribbon" in lowercase_sku:
        updated_addon_list[0] = True

    for music_option in MUSIC_BOX_SKUS:
        if str(music_option).lower() in lowercase_sku:
            updated_addon_list[1].append(str(music_option))

    if "polaroid" in lowercase_sku:
        updated_addon_list[2] = True

    for scent_option in SCENT_SKUS:
        if str(scent_option).lower() in lowercase_sku:
            updated_addon_list[3].append(str(scent_option))

    return updated_addon_list

# can use this later to show delivery type
def get_delivery_type(order, item):
    delivery_type = None
    for prop in item["properties"]:
        if prop["name"] == "Selection":
            delivery_type = prop["value"]
            break
    if "delivery" in order["tags"].lower():
            delivery_type = "Delivery"
    if "pickup" in order["tags"].lower() or "pick up" in order["tags"].lower():
        delivery_type = "Pickup"
    return delivery_type
    

# main function to process orders
def process_orders():
    orders = get_orders()

    # looping through json of retrieved orders
    # and extracting the necessary order details
    rows = []
    for order in orders:
        for item in order["line_items"]:
            rows.append({
                "order": order["name"],
                "tags": order["tags"],
                "sku": item["sku"],
                "product": item["title"],
                "qty": item["quantity"],
                "delivery_date": standardise_date(get_delivery_date(order, item)),
                "delivery_slot": get_delivery_slot(order, item),
                "delivery_type": get_delivery_type(order, item)
            })

    df = pd.DataFrame(rows)

    # merge add-ons with main orders
    processed_rows = []
    for order_id, group in df.groupby("order"):
        ribbon = False
        music_box = []
        polaroid = False
        scent = []
        main_sku = None
        qty = None
        delivery_date = None
        delivery_slot = None
        delivery_type = None
        custom_details = ""

        for _, row in group.iterrows():
            sku = row["sku"]
            if is_ribbon(sku):
                ribbon = True
            elif is_music_box(sku):
                music_box.append(sku)
            elif is_polaroid(sku):
                polaroid = True
            elif is_scent(sku):
                scent.append(sku)
            else:
                if main_sku is not None: 
                    main_sku = f"COMPLEX ORDER (>1 main item)"
                    break
                main_sku = sku
                qty = row["qty"]
                delivery_date = row["delivery_date"]
                delivery_slot = row["delivery_slot"]
                delivery_type = row["delivery_type"]

        if pd.isna(main_sku) or str(main_sku).strip() == "":
            main_sku = "CUSTOM ORDER (Please check details manually)"
            custom_details = row["product"]

        [ribbon, music_box, polaroid, scent] = update_addons_using_sku(main_sku, ribbon, music_box, polaroid, scent)
        

        processed_rows.append({
            "Order": order_id,
            "SKU": main_sku,
            "Custom Details": custom_details,
            "Quantity": qty,
            "Ribbon": ribbon,
            "Music Box": music_box,
            "Polaroid": polaroid,
            "Scent": scent,
            "Delivery Slot": delivery_slot,
            "Delivery Date": delivery_date,
            "Delivery Type": delivery_type
        })

    processed_df = pd.DataFrame(processed_rows)

    # only keep relevant orders from today onwards
    today = pd.Timestamp.now(tz="Asia/Singapore").date()
    processed_df["Delivery Date"] = pd.to_datetime(
    processed_df["Delivery Date"], errors="coerce").dt.date
    current_orders_df = processed_df[processed_df["Delivery Date"] >= today]

    # sort orders
    sorted_processed_df = current_orders_df.sort_values(by=["Delivery Date", "Delivery Slot", "SKU"])
    sorted_processed_df.to_csv("sorted_processed_df.csv", index=False)

    # included completed status columns
    completed_orders = cleanup_completed_orders(
        sorted_processed_df["Order"].tolist()
    )

    sorted_processed_df["Completed"] = (
        sorted_processed_df["Order"]
        .map(lambda x: completed_orders.get(x, False))
    )

    return  sorted_processed_df


