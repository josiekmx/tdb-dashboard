import json
import os

FILE_NAME = "../data/completed_orders.json"


def load_completed_orders():
    if not os.path.exists(FILE_NAME):
        return {}

    with open(FILE_NAME, "r") as f:
        return json.load(f)


def save_completed_orders(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=4)


def set_completed(order_id, completed):
    data = load_completed_orders()

    if completed:
        data[order_id] = True
    else:
        data.pop(order_id, None)

    save_completed_orders(data)


def cleanup_completed_orders(active_order_ids):
    data = load_completed_orders()

    active_order_ids = set(active_order_ids)

    cleaned = {
        order_id: value
        for order_id, value in data.items()
        if order_id in active_order_ids
    }

    save_completed_orders(cleaned)

    return cleaned