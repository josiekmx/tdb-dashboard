import streamlit as st
from order_processor import process_orders
from components.authentication import check_password

# displays login page to authenticate users
if not check_password():
    st.stop()

# set windows tab
st.set_page_config(
    page_title="The Daily Blooms Dashboard",
    page_icon="🌸",
    layout="wide"
)

# dashboard header
st.header("The Daily Blooms Dashboard 🌸")

df = process_orders()

# display drop down menu to select date and delivery/pickup slot
dates = sorted(df["Delivery Date"].dropna().unique())

selected_date = st.selectbox(
    "Delivery Date",
    dates
)

slots = sorted(df["Delivery Slot"].dropna().unique())
selected_slots = st.multiselect(
    "Time Slot(s)",
    options=slots
)

# filter orders according to data and delivery/pickup slot
filtered = df[
    df["Delivery Date"] == selected_date
]
if selected_slots:
    filtered = filtered[
        filtered["Delivery Slot"].isin(selected_slots)
    ]
else:
    # If nothing is selected, show no rows
    filtered = filtered.iloc[0:0]


filtered = filtered.sort_values(by="SKU")
display_df = filtered.drop(columns=['Delivery Date', 'Delivery Slot'])


row_height = 35        # Approximate height of each row (pixels)
header_height = 38     # Header height
max_height = 700       # Don't let it grow indefinitely

height = min(header_height + len(display_df) * row_height, max_height)

st.dataframe(
    display_df,
    use_container_width=True,
    height=height
)

st.markdown("<br>", unsafe_allow_html=True)

# summary tables 

delivery_orders = filtered[filtered["Delivery Type"] == "Delivery"]
pickup_orders = filtered[filtered["Delivery Type"] == "Pickup"]
missing_delivery_orders = filtered[filtered["Delivery Type"].isna()]

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Deliveries")
    st.metric("Total Orders", len(delivery_orders))

    delivery_summary = (
        delivery_orders.groupby("SKU")
        .size()
        .reset_index(name="Count")
        .sort_values("SKU")
    )

    st.dataframe(
        delivery_summary,
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.markdown("### Pickups")
    st.metric("Total Orders", len(pickup_orders))

    pickup_summary = (
        pickup_orders.groupby("SKU")
        .size()
        .reset_index(name="Count")
        .sort_values("SKU")
    )

    st.dataframe(
        pickup_summary,
        use_container_width=True,
        hide_index=True
    )

with col3:
    st.markdown("### Missing Delivery Type")
    st.metric("Total Orders", len(missing_delivery_orders))

    missing_delivery_summary = (
        missing_delivery_orders.groupby("SKU")
        .size()
        .reset_index(name="Count")
        .sort_values("SKU")
    )

    st.dataframe(
        missing_delivery_summary,
        use_container_width=True,
        hide_index=True
    )