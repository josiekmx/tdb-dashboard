import streamlit as st
from order_processor import process_orders
from services.google_sheet import save_assignments

def display_order_details_table():
    df = process_orders()

    # display drop down menu to select date and delivery/pickup slot
    dates = sorted(df["Delivery Date"].dropna().unique())

    selected_date = st.selectbox(
        "Delivery Date",
        dates,
        index=0 if st.session_state.get("selected_date") is None
            else dates.index(st.session_state.selected_date),
        key="selected_date"
    )

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

    # sort by sku

    # slot_order = {
    #     "9:00 AM - 2:00 PM": 1,
    #     "1:00 PM - 6:00 PM": 2,
    #     "5:00 PM - 10:00 PM": 3,
    #     "Pick up": 4,
    #     "Custom": 5
    # }

    # filtered["Slot Order"] = filtered["Delivery Slot"].map(slot_order).fillna(999)
    # filtered = filtered.sort_values(
    #     by=["SKU", "Completed", "Slot Order"],
    #     ascending=[True, True, True]
    # )
    # filtered = filtered.drop(columns=["Slot Order"])
    # display_df = filtered.drop(columns=['Delivery Date'])

    filtered = filtered.sort_values(by="SKU")
    display_df = filtered.drop(columns=['Delivery Date'])


    # optimise table size
    row_height = 35 
    header_height = 38
    max_height = 700
    height = min(header_height + len(display_df) * row_height, max_height)


    disabled = [
        c for c in display_df.columns
        if c not in ["Assignee", "Completed"]
    ]
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        height=height,
        hide_index=True,
        disabled=disabled,
        column_config={
            "Assignee": st.column_config.SelectboxColumn(
                "Assignee",
                options=["","Justin", "Josie", "Puiyee", "Enie"]
            ),
            "Completed": st.column_config.CheckboxColumn(
                "Completed"
            )
        }
    )

    # insert empty space to optimise ui
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Save Changes"):
        assignment_updates = edited_df[
            ["Order", "Assignee", "Completed"]
        ]
        save_assignments(assignment_updates)
        st.success("Assignments saved")

    # insert empty space to optimise ui
    st.markdown("<br>", unsafe_allow_html=True)

    return filtered