import streamlit as st
from order_processor import process_orders
from completion_store import set_completed

def display_order_details_table():
    df = process_orders()

    # display drop down menu to select date
    dates = sorted(df["Delivery Date"].dropna().unique())
    # If no date has been selected yet, default to the first date
    if not st.session_state.get("selected_date"):
        st.session_state.selected_date = dates[0]
    selected_date = st.selectbox(
        "Delivery Date",
        options=dates,
        key="selected_date",
    )

    # display drop down menu to select timeslot
    slots = sorted(df["Delivery Slot"].dropna().unique())
    # If nothing is selected, automatically select every slot
    if not st.session_state.get("selected_slots"):
        st.session_state.selected_slots = slots
    selected_slots = st.multiselect(
        "Time Slot(s)",
        options=slots,
        key="selected_slots",
    )

    # filter orders according to data and delivery/pickup slot
    filtered = df[df["Delivery Date"] == selected_date]
    if selected_slots:
        filtered = filtered[filtered["Delivery Slot"].isin(selected_slots)]
    else:
        # If nothing is selected, show no rows
        filtered = filtered.iloc[0:0]

    # sort orders in terms of timeslot
    slot_order = {
        "9:00 AM - 2:00 PM": 1,
        "1:00 PM - 6:00 PM": 2,
        "5:00 PM - 10:00 PM": 3,
        "Pick up": 4,
        "Custom": 5
    }
    filtered["Slot Order"] = filtered["Delivery Slot"].map(slot_order).fillna(999)
    filtered = filtered.sort_values(
        by=["Slot Order", "SKU"],
        ascending=[True, True]
    )
    filtered = filtered.drop(columns=["Slot Order"])
    display_df = filtered.drop(columns=['Delivery Date'])


    # optimise table size
    row_height = 35 
    header_height = 38
    max_height = 700
    height = min(header_height + len(display_df) * row_height, max_height)

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        height=height,
        hide_index=True,
        column_config={
            "Completed": st.column_config.CheckboxColumn(
                "Completed"
            )
        },
        disabled=[
            col for col in display_df.columns
            if col != "Completed"
        ]
    )

    for _, row in edited_df.iterrows():
        order_id = row["Order"]
        completed = row["Completed"]

        if completed != filtered.loc[
            filtered["Order"] == order_id,
            "Completed"
        ].iloc[0]:
            set_completed(order_id, completed)

    # insert empty space to optimise ui
    st.markdown("<br>", unsafe_allow_html=True)

    return filtered