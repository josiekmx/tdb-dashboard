# The Daily Blooms Dashboard

A Streamlit dashboard that automates the processing of Shopify orders for The Daily Blooms.

Instead of manually exporting Shopify orders into Excel and sorting them at each delivery time slot, this dashboard retrieves open orders directly from the Shopify Admin API, processes them into a reader friendly format, and provides order summaries for order preparation.

---

## Features

- Retrieves the latest 250 open Shopify orders
- Extracts and displays key order information:
  - Order ID
  - SKU
  - Custom Order Details
  - Quantity 
  - Ribbon Add-ons
  - Music Boxes Add-ons
  - Polaroid Add-ons
  - Scents Add-ons 
  - Delivery Time Slot
  - Delivery Type
  - Completion Status 
- Filters orders by date and timeslot
- Sorts orders by:
  1. Delivery slot
  2. Completion status (Completed items at the bottom)
  3. SKU
- Generates Delivery and Pickup Summary Tables
- Password protected using Streamlit authentication
- Enables refresh to update dashboard order details with the latest orders
- Orders can be marked and unmarked as completed

---

# Project Structure

```
TDB_ORDER_DASHBOARD
│
├── dashboard.py
├── order_processor.py
├── shopify_client.py
│
├── components/
│   ├── authentication.py
│   ├── order_details_table.py
│   └── order_summary_tables.py
│
├── .streamlit/
│   └── config.toml
│
├── assets/
│   └── flower_logo.png
│
├── requirements.txt
└── README.md
```

---

# File Overview

## dashboard.py

Entry point of the application.

Responsibilities:
- Sets page configuration
- Displays dashboard components:
  - Login Page
  - Refresh Button
  - Order details table
  - Summary tables

---

## shopify_client.py

Responsible for communicating with the Shopify Admin API.

#### Functions: 

1. get_orders()

   Retrieves orders from shopify database and returns the latest 250 open orders created in json format. Note that it can only retrieve a **maximum of 250 open orders**.

2. update_order_completed()

   Updates the completion status of a specific order in Shopify by adding or removing the tdb_completed tag. When the completed variable is True, the function adds the tag to the order if it is not already present. When the completed variable is False, it removes the tdb_completed tag if it exists. The function first retrieves the order's current tags to ensure that existing tags are preserved, then sends the updated tag list using the Shopify Admin API.

---

## order_processor.py

Processes raw Shopify order data into a structured dataframe for display in the dashboard.

Responsibilities:
- Extracting relevant information from raw Shopify orders.
- Merging add-on products (e.g. ribbons, music boxes, scents) with their corresponding main product.
- Detecting complex or custom orders that require manual review.
- Filtering out past orders.
- Returning a sorted DataFrame ready for the Streamlit frontend.

#### Helper Functions

| Function | Description |
|----------|-------------|
| `is_ribbon(sku)` | Returns whether the SKU represents a ribbon add-on. |
| `is_music_box(sku)` | Returns whether the SKU is a recognised music box add-on. |
| `is_polaroid(sku)` | Returns whether the SKU represents a polaroid add-on. |
| `is_scent(sku)` | Returns whether the SKU is a recognised scent add-on. |
| `get_delivery_date(order, item)` | Extracts the delivery date from Shopify line item properties or order tags. Handles date-change orders and multiple date formats. |
| `standardise_date(date_str)` | Converts supported date formats into the standard `YYYY-MM-DD` format. |
| `get_delivery_slot(order, item)` | Determines the delivery timeslot or pickup request based on Shopify order tags. |
| `update_addons_using_sku(...)` | Detects add-ons embedded within the main product SKU (e.g. `F-Ribbon-Polaroid-FRE50`) and updates the corresponding add-on fields. |
| `get_delivery_type(order, item)` | Determines whether the order is a delivery or pickup using both line item properties and order tags. |

#### Functions

1. process_orders()

   Retrieves raw Shopify orders and converts them into a dashboard ready DataFrame.

   The function performs the following steps:

        1. Retrieves the latest open orders from Shopify.
        2. Extracts relevant information from every line item.
        3. Groups line items belonging to the same customer order.
        4. Merges add-on products into their corresponding main order.
        5. Detects:
           - Complex orders containing multiple main products.
           - Custom orders without a SKU, then attaching custom order details
        6. Standardises delivery dates.
        7. Filters out orders with delivery dates before today.
        8. Sorts remaining orders by:
           - Delivery Date
           - Delivery Slot
           - SKU
        9. Returns the processed DataFrame.

#### Notes
- Orders containing more than one main product are labelled as **`COMPLEX ORDER (>1 main item)`** for manual review.
- Orders without a SKU are labelled as **`CUSTOM ORDER (Please check details manually)`**.
- Only orders with delivery dates from the current day onwards are returned.

---

## components/authentication.py

Checks whether the user is password aunthenticated. Otherwise, user is directed to the login page.

#### Functions: 

1. check_password()

   Uses ```st.secrets["APP_PASSWORD"]```to restrict dashboard access.

---

## components/order_details_table.py

Displays the main order details table within the Streamlit dashboard.

#### Functions

1. display_order_details_table()
        
        1. Retrieves processed order data using `process_orders()`.
        2. Displays a dropdown menu allowing the user to select a delivery date.
        3. Displays a multi-select widget allowing one or more delivery slots to be selected.
        4. Filters orders according to the selected date and delivery slot(s).
        5. Sorts the filtered orders by:
           - Delivery Slot
           - Completed Status
           - SKU
        6. Dynamically calculates the table height based on the number of displayed rows (up to a maximum height).
        7. Displays the filtered orders using Streamlit's `st.data_editor()` where all columns are in read only format except the completed status column.
        8. Returns the filtered DataFrame for use by downstream dashboard components (e.g. summary tables).

#### Notes

- The first available delivery date is selected by default when the dashboard loads.
- All available delivery slots are selected by default.
---

## components/order_summary_tables.py

Displays summary tables for delivery and pickup orders.

Responsibilities:
- Separating filtered orders into deliveries and pickups.
- Displaying the total number of delivery and pickup orders.
- Summarising the number of orders for each SKU.

#### Functions

1. display_order_summary_tables()

   Displays summary statistics for the currently filtered orders.

   The function performs the following steps:

        1. Separates the filtered orders into:
           - Delivery orders.
           - Pickup orders.
        2. Calculates the total number of delivery orders and displays the result as a metric.
        3. Groups delivery orders by SKU and counts the number of occurrences of each SKU.
        4. Displays the delivery summary table.
        5. Repeats the same process for pickup orders.

---

# Processing Data Pipeline

```
Shopify Orders
        │
        ▼
shopify_client.py
        │
        ▼
Raw JSON
        │
        ▼
order_processor.py
        │
        ▼
Processed DataFrame
        │
        ▼
order_details_table.py
        │
        ▼
order_summary_table.py
        │
        ▼
Dashboard
```

---

# Configuration

Secrets are stored using Streamlit Secrets.

Required values:

```
SHOP=
TOKEN=
APP_PASSWORD=
```

Do **not** commit these values into GitHub. In the case of accidental commits, rotate api keys.

s---


---
