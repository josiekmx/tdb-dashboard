import streamlit as st
from order_processor import process_orders

def display_order_details_table():
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

    return filtered