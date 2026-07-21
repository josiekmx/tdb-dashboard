import streamlit as st
from order_processor import process_orders
from services.google_sheet import save_assignments

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
    filtered = df[df["Delivery Date"] == selected_date]
    if selected_slots:
        filtered = filtered[filtered["Delivery Slot"].isin(selected_slots)]
    else:
        # If nothing is selected, show no rows
        filtered = filtered.iloc[0:0]

    # sort by sku
    filtered = filtered.sort_values(by="SKU")
    display_df = filtered.drop(columns=['Delivery Date', 'Delivery Slot'])


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

    if st.button("Save Changes"):
        assignment_updates = edited_df[
            ["Order", "Assignee", "Completed"]
        ]
        save_assignments(assignment_updates)
        st.success("Assignments saved")

    # insert empty space to optimise ui
    st.markdown("<br>", unsafe_allow_html=True)

    return filtered