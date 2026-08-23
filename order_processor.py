import pandas as pd
from shopify_client import get_orders, ASSIGNEES
import re
from datetime import datetime
import json
import os 
import streamlit as st

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

def get_assignee(tags):
    for name, tag in ASSIGNEES.items():
        if tag in tags:
            return name
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
    tags = order["tags"]

    # Pickup: show the actual selected pickup time window
    if "pickup" in tags.lower() or "pick up" in tags.lower():
        pickup_timeslot = get_pickup_timeslot(item)

        if pickup_timeslot:
            return f"Pick up {pickup_timeslot}"

        return "Pick up"

    # Delivery: use the current timeslot from Shopify tags
    if "9:00 AM - 2:00 PM" in tags:
        return "9:00 AM - 2:00 PM"

    elif "1:00 PM - 6:00 PM" in tags:
        return "1:00 PM - 6:00 PM"

    elif "5:00 PM - 10:00 PM" in tags:
        return "5:00 PM - 10:00 PM"

    # Irregular category
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

# Get the customer's selected pickup time window from line item properties
def get_pickup_timeslot(item):
    for prop in item.get("properties", []):
        if prop.get("name") in [
            "Pickup Timeslot Weekday",
            "Pickup Timeslot Weekend",
        ]:
            value = prop.get("value")

            if value:
                return value

    return None    

# main function to process orders
def process_orders():
    orders = get_orders()

    # looping through json of retrieved orders
    # and extracting the necessary order details
    rows = []
    for order in orders:
        for item in order["line_items"]:
            rows.append({
                "shopify_id": order["id"],
                "order": order["name"],
                "tags": order["tags"],
                "sku": item["sku"],
                "product": item["title"],
                "qty": item["quantity"],
                "delivery_date": standardise_date(get_delivery_date(order, item)),
                "delivery_slot": get_delivery_slot(order, item),
                "delivery_type": get_delivery_type(order, item),
                "completed": "tdb_completed" in order["tags"],
                "assignee": get_assignee(order["tags"])
            })

    df = pd.DataFrame(rows)

    # merge add-ons order items with main orders
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
        shopify_id = None
        completed = False
        assignee = None

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
                # indicates that there is another item within
                # the same order, which is a main item and 
                # not a typical add-on item
                if main_sku is not None: 
                    main_sku = f"COMPLEX ORDER (>1 main item)"
                    break
                main_sku = sku
                qty = row["qty"]
                delivery_date = row["delivery_date"]
                delivery_slot = row["delivery_slot"]
                delivery_type = row["delivery_type"]
                shopify_id = row["shopify_id"]
                assignee = row["assignee"]
                completed = row["completed"]
                

        # catches custom orders where sku is None
        if pd.isna(main_sku) or str(main_sku).strip() == "":
            main_sku = "CUSTOM ORDER (Please check details manually)"
            custom_details = row["product"] 

        [ribbon, music_box, polaroid, scent] = update_addons_using_sku(main_sku, ribbon, music_box, polaroid, scent)
        

        processed_rows.append({
            "Assignee": assignee,
            "Completed": completed,
            "Shopify ID": shopify_id,
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
    processed_df["Delivery Date"] = pd.to_datetime(processed_df["Delivery Date"], errors="coerce").dt.date
    current_orders_df = processed_df[processed_df["Delivery Date"] >= today]

    # sort orders
    sorted_processed_df = current_orders_df.sort_values(by=["Delivery Date", "Delivery Slot", "SKU"])

    return  sorted_processed_df


