import pandas as pd
import streamlit as st

from order_processor import process_orders
from shopify_client import (
    update_order_completed,
    update_order_assignee,
    ASSIGNEES,
)


# Display unfulfilled order counts by AM / PM / NIGHT
def display_timeslot_summary(df, selected_date):
    date_orders = df[
        df["Delivery Date"] == selected_date
    ]

    slot_groups = {
        "AM": {
            "delivery": ["9:00 AM - 2:00 PM"],
            "pickup": ["Pick up 9:00 AM - 12:00 PM"],
        },
        "PM": {
            "delivery": ["1:00 PM - 6:00 PM"],
            "pickup": [
                "Pick up 12:00 PM - 3:00 PM",
                "Pick up 3:00 PM - 5:00 PM",
            ],
        },
        "NIGHT": {
            "delivery": ["5:00 PM - 10:00 PM"],
            "pickup": ["Pick up 5:00 PM - 9:00 PM"],
        },
    }

    cols = st.columns(3)

    for col, (label, slots) in zip(
        cols,
        slot_groups.items()
    ):
        delivery_count = date_orders[
            (date_orders["Delivery Type"] == "Delivery")
            & date_orders["Delivery Slot"].isin(
                slots["delivery"]
            )
        ]["Order"].nunique()

        pickup_count = date_orders[
            (date_orders["Delivery Type"] == "Pickup")
            & date_orders["Delivery Slot"].isin(
                slots["pickup"]
            )
        ]["Order"].nunique()

        total_count = delivery_count + pickup_count

        # Display the summary card for this timeslot
        with col:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #ddd8d2;
                    border-radius: 12px;
                    padding: 20px 24px;
                    min-height: 165px;
                ">
                    <div style="
                        font-size: 18px;
                        margin-bottom: 6px;
                    ">
                        {label} Unfulfilled
                    </div>

                    <div style="
                        font-size: 42px;
                        line-height: 1.2;
                        margin-bottom: 20px;
                    ">
                        {total_count}
                    </div>

                    <div style="
                        display: flex;
                        gap: 32px;
                    ">
                        <div>
                            <div style="font-size: 13px; opacity: 0.65;">
                                Delivery
                            </div>
                            <div style="font-size: 24px; font-weight: 600;">
                                {delivery_count}
                            </div>
                        </div>

                        <div>
                            <div style="font-size: 13px; opacity: 0.65;">
                                Pick Up
                            </div>
                            <div style="font-size: 24px; font-weight: 600;">
                                {pickup_count}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

def display_order_details_table():
    df = process_orders()

    # ---------------------------------------------------------
    # DELIVERY DATE FILTER
    # ---------------------------------------------------------

    dates = sorted(
        df["Delivery Date"]
        .dropna()
        .unique()
    )

    if not dates:
        st.info("No upcoming orders found.")
        return df

    # If no date has been selected yet, default to first date
    if not st.session_state.get("selected_date"):
        st.session_state.selected_date = dates[0]

    selected_date = st.selectbox(
        "Delivery Date",
        options=dates,
        key="selected_date",
    )

    # ---------------------------------------------------------
    # TIME SLOT FILTER
    # ---------------------------------------------------------

    raw_slots = sorted(
        df["Delivery Slot"]
        .dropna()
        .unique()
    )

    # Keep delivery slots as normal,
    # but group all pickup windows under one "Pick up" filter
    slots = [
        slot
        for slot in raw_slots
        if not str(slot).startswith("Pick up")
    ]

    # Add one generic Pick up filter if pickup orders exist
    if any(
        str(slot).startswith("Pick up")
        for slot in raw_slots
    ):
        slots.append("Pick up")

    # If nothing is selected, automatically select every slot
    if not st.session_state.get("selected_slots"):
        st.session_state.selected_slots = slots

    selected_slots = st.multiselect(
        "Time Slot(s)",
        options=slots,
        key="selected_slots",
    )

    # Show unfulfilled workload for the selected date
    display_timeslot_summary(
        df,
        selected_date
    )

    # ---------------------------------------------------------
    # FILTER ORDERS
    # ---------------------------------------------------------

    filtered = df[
        df["Delivery Date"] == selected_date
    ].copy()

    if selected_slots:
        slot_masks = []

        for slot in selected_slots:

            # "Pick up" matches every pickup time window
            if slot == "Pick up":
                slot_masks.append(
                    filtered["Delivery Slot"]
                    .astype(str)
                    .str.startswith("Pick up")
                )

            else:
                slot_masks.append(
                    filtered["Delivery Slot"] == slot
                )

        combined_mask = slot_masks[0]

        for mask in slot_masks[1:]:
            combined_mask = (
                combined_mask | mask
            )

        filtered = filtered[
            combined_mask
        ].copy()

    else:
        # If nothing is selected, show no rows
        filtered = filtered.iloc[0:0].copy()

    # ---------------------------------------------------------
    # SORT ORDERS BY TIMESLOT
    # ---------------------------------------------------------

    slot_order = {
        "9:00 AM - 2:00 PM": 1,
        "1:00 PM - 6:00 PM": 2,
        "5:00 PM - 10:00 PM": 3,
        "Custom Time": 5,
    }

    # All pickup windows appear after normal delivery slots
    filtered["Slot Order"] = (
        filtered["Delivery Slot"].apply(
            lambda slot:
                4
                if str(slot).startswith("Pick up")
                else slot_order.get(slot, 999)
        )
    )

    filtered = filtered.sort_values(
        by=[
            "Slot Order",
            "Completed",
            "SKU",
        ],
        ascending=[
            True,
            True,
            True,
        ],
    )

    filtered = filtered.drop(
        columns=["Slot Order"]
    )

    # Delivery Date is already selected above,
    # so we don't need to show it in the table
    display_df = filtered.drop(
        columns=["Delivery Date"]
    )

    # ---------------------------------------------------------
    # TABLE SIZE
    # ---------------------------------------------------------

    row_height = 35
    header_height = 38
    max_height = 700

    height = min(
        header_height
        + len(display_df) * row_height,
        max_height,
    )

    # ---------------------------------------------------------
    # EDITABLE ORDER TABLE
    # ---------------------------------------------------------

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        height=height,
        hide_index=True,
        column_config={
            "Shopify ID": None,

            "Completed":
                st.column_config.CheckboxColumn(
                    "Completed"
                ),

            "Assignee":
                st.column_config.SelectboxColumn(
                    "Assignee",
                    options=list(
                        ASSIGNEES.keys()
                    ),
                    required=False,
                ),
        },

        # Only Completed and Assignee can be edited
        disabled=[
            col
            for col in display_df.columns
            if col not in [
                "Completed",
                "Assignee",
            ]
        ],
    )

    # ---------------------------------------------------------
    # UPDATE SHOPIFY WHEN TABLE IS EDITED
    # ---------------------------------------------------------

    updated = False

    for _, row in edited_df.iterrows():
        shopify_id = row["Shopify ID"]

        # -----------------------------------------------------
        # COMPLETED STATUS
        # -----------------------------------------------------

        original_completed = filtered.loc[
            filtered["Shopify ID"]
            == shopify_id,
            "Completed",
        ].iloc[0]

        if (
            row["Completed"]
            != original_completed
        ):
            changed = update_order_completed(
                shopify_id,
                row["Completed"],
            )

            updated = (
                updated or changed
            )

        # -----------------------------------------------------
        # ASSIGNEE
        # -----------------------------------------------------

        original_assignee = filtered.loc[
            filtered["Shopify ID"]
            == shopify_id,
            "Assignee",
        ].iloc[0]

        new_assignee = row["Assignee"]

        # Blank means no assignee
        if pd.isna(original_assignee):
            original_assignee = None

        if pd.isna(new_assignee):
            new_assignee = None

        if (
            new_assignee
            != original_assignee
        ):
            changed = update_order_assignee(
                shopify_id,
                new_assignee,
            )

            updated = (
                updated or changed
            )

    # Rerun so dashboard reflects Shopify updates
    if updated:
        st.rerun()

    # ---------------------------------------------------------
    # UI SPACING
    # ---------------------------------------------------------

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    return filtered