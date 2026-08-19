# dataclass is a Python helper that makes it easier to create
# structured data objects without writing lots of boilerplate code.
from dataclasses import dataclass, field

# Optional means a value is allowed to be None / missing.
# For example, an order might temporarily have no recipient phone.
from typing import Optional


# ============================================================
# DELIVERY LINE ITEM
# ============================================================
# Represents ONE product / line item inside a Shopify order.
#
# Example:
# Order #TDB123 contains:
#
#   2 × Bloom Box        SKU: F
#   1 × Music Box        SKU: Music-HDB
#
# These would become two DeliveryLineItem objects.
#
# We keep every line item because we will later use the SKU
# and quantity to calculate the number of tags required.
# ============================================================

@dataclass
class DeliveryLineItem:
    sku: str
    product: str
    quantity: int


# ============================================================
# TDB DELIVERY ORDER
# ============================================================
# This represents ONE complete TDB order inside our
# Detrack integration.
#
# Shopify's raw data will first be converted into this format.
#
# Shopify
#     ↓
# TDBDeliveryOrder
#     ↓
# Validation
#     ↓
# Detrack Mapper
#     ↓
# Detrack
#
# This means Detrack does not need to understand Shopify's
# complicated raw order structure directly.
# ============================================================

@dataclass
class TDBDeliveryOrder:

    # --------------------------------------------------------
    # SHOPIFY IDENTIFIERS
    # --------------------------------------------------------

    # Shopify's permanent internal ID.
    # We will eventually use this for things such as
    # duplicate-upload prevention.
    shopify_id: str

    # The human-readable order number that your team sees.
    # Example: "#12345"
    order_number: str


    # --------------------------------------------------------
    # DELIVERY INFORMATION
    # --------------------------------------------------------

    # The requested delivery date.
    # Example: "2026-08-20"
    #
    # Optional because an invalid Shopify order might not
    # contain a delivery date. Our validator will catch this.
    delivery_date: Optional[str]

    # Example:
    # "9:00 AM - 2:00 PM"
    # "1:00 PM - 6:00 PM"
    # "5:00 PM - 10:00 PM"
    # "Custom Time"
    delivery_slot: Optional[str]

    # Usually:
    # "Delivery"
    # or
    # "Pick Up"
    #
    # Pickup orders will eventually be excluded from
    # the Detrack upload.
    delivery_type: Optional[str]


    # --------------------------------------------------------
    # RECIPIENT INFORMATION
    # --------------------------------------------------------

    # Person receiving the flowers.
    recipient_name: Optional[str] = None

    # Recipient's contact number.
    recipient_phone: Optional[str] = None


    # --------------------------------------------------------
    # ADDRESS
    # --------------------------------------------------------

    # Full delivery address.
    address: Optional[str] = None

    # Singapore postal code.
    postal_code: Optional[str] = None


    # --------------------------------------------------------
    # CUSTOMER REQUESTS / REMARKS
    # --------------------------------------------------------

    # Any additional request entered for the order.
    #
    # We keep the original wording rather than automatically
    # summarising it because these instructions may be
    # operationally important.
    additional_request: Optional[str] = None


    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    # Contains ALL products belonging to this Shopify order.
    #
    # Example:
    #
    # [
    #     DeliveryLineItem(
    #         sku="Basket-Pink",
    #         product="Pink Flower Basket",
    #         quantity=2
    #     ),
    #     DeliveryLineItem(
    #         sku="Music-HDB",
    #         product="Music Box",
    #         quantity=1
    #     )
    # ]
    #
    # default_factory=list simply means:
    # start with an empty list if there are no items yet.
    line_items: list[DeliveryLineItem] = field(default_factory=list)


    # --------------------------------------------------------
    # TAG CALCULATION
    # --------------------------------------------------------

    # Total number of physical tags required for this order.
    #
    # We will calculate this later using:
    #
    # SKU
    #   ↓
    # SKU Tag Mapping
    #   ↓
    # tags per product × quantity
    #   ↓
    # total number of tags
    #
    # None means it has not been calculated yet.
    number_of_tags: Optional[int] = None


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    # Overall status of this order.
    #
    # Possible statuses:
    #
    # READY
    # WARNING
    # ERROR
    #
    # We start at READY and the validator can change it.
    validation_status: str = "READY"

    # Stores the reasons for WARNING or ERROR.
    #
    # Example:
    #
    # [
    #     "Recipient phone is missing",
    #     "SKU ABC123 has no tag mapping"
    # ]
    validation_messages: list[str] = field(default_factory=list)


    # --------------------------------------------------------
    # DETRACK SYNC INFORMATION
    # --------------------------------------------------------

    # Indicates whether this order has already been
    # uploaded to Detrack.
    #
    # Initially every order is NOT_SYNCED.
    detrack_sync_status: str = "NOT_SYNCED"

    # Once Detrack successfully creates the delivery job,
    # we can store its ID here.
    #
    # This will later help with:
    # - duplicate prevention
    # - sync history
    # - updating Detrack jobs
    detrack_job_id: Optional[str] = None