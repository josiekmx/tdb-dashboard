# 🌸 The Daily Blooms Dashboard

A Streamlit dashboard that automates the processing of Shopify orders for The Daily Blooms.

Instead of manually exporting Shopify orders into Excel and sorting them at each delivery time slot, this dashboard retrieves open orders directly from the Shopify Admin API, processes them into a florist-friendly format, and provides order summaries for bouquet preparation.

---

## Features

- Retrieves the latest open Shopify orders
- Extracts delivery date and delivery time slot
- Identifies:
  - Ribbon add-ons
  - Music box add-ons
  - Polaroid add-ons
  - Scent add-ons
- Detects custom and complex orders
- Groups add-on products with their corresponding bouquet
- Automatically sorts orders by:
  - Delivery slot
  - SKU
- Generates SKU summary tables
- Password protected using Streamlit authentication

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
├── services/
│
├── debug/
│
├── .streamlit/
│   └── config.toml
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
- Authenticates user
- Displays dashboard title
- Displays:
  - Order details table
  - Summary tables

Execution flow:

```
Authenticate User
        ↓
Process Shopify Orders
        ↓
Display Order Table
        ↓
Display Summary Tables
```

---

## shopify_client.py

Responsible for communicating with the Shopify Admin API.

Main function:

```python
get_orders()
```

Retrieves the latest open Shopify orders.

Current implementation:

- Uses Shopify REST Admin API
- Retrieves a maximum of **250 open orders**

```
Shopify
    ↓
REST API Request
    ↓
JSON Response
```

**Note**

Shopify limits each API request to 250 records.

If the shop ever exceeds 250 open orders simultaneously, pagination should be implemented.

---

## order_processor.py

Core processing logic of the application.

Converts raw Shopify JSON into the dashboard dataframe.

Major responsibilities:

### 1. Parse Shopify JSON

Extracts:

- Order number
- SKU
- Product
- Quantity
- Delivery date
- Delivery slot
- Delivery type

---

### 2. Detect add-ons

Recognises add-on products such as:

- Ribbon
- Music Box
- Polaroid
- Scent

These are merged into their corresponding bouquet order.

---

### 3. Handle custom orders

Orders with:

- missing SKU
- multiple bouquet SKUs

are labelled as:

```
CUSTOM ORDER
```

or

```
COMPLEX ORDER
```

to alert staff that manual review is required.

---

### 4. Clean data

Includes helper functions to:

- standardise delivery dates
- determine delivery slot
- determine delivery type

---

### 5. Produce dashboard dataframe

Final dataframe contains fields such as:

| Column |
|----------|
| Order |
| SKU |
| Quantity |
| Ribbon |
| Music Box |
| Polaroid |
| Scent |
| Delivery Slot |
| Delivery Date |
| Delivery Type |
| Custom Details |

---

## components/authentication.py

Simple password authentication.

Uses:

```
st.secrets["APP_PASSWORD"]
```

to restrict dashboard access.

---

## components/order_details_table.py

Displays the main dashboard table.

Responsibilities:

- Delivery date selector
- Time slot selector
- Sort orders
- Display processed dataframe

Orders are sorted by:

1. Delivery Slot
2. SKU

---

## components/order_summary_tables.py

Creates summary tables used by florists.

Examples:

- SKU counts
- Delivery totals
- Pickup totals

These provide a quick overview of the number of bouquets required for each SKU.

---

# Processing Pipeline

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
Summary Tables
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

Do **not** commit these values into GitHub.

---

# Running the Dashboard

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
streamlit run dashboard.py
```

---

# Dependencies

Main libraries:

- streamlit
- pandas
- requests

See `requirements.txt` for the full list.

---

# Future Improvements

Potential future enhancements include:

- Shopify pagination (retrieve >250 open orders)
- Live auto-refresh
- Google Sheets integration for staff assignment
- Order completion tracking
- Automatic colour-coding by delivery slot
- Better handling of complex custom orders
- Search by order number
- Export filtered orders to CSV

---

# Author

Developed by Janna Leong

For The Daily Blooms