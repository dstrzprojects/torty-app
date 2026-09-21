import uuid

import streamlit as st


CART_KEY = "valuation_items"


def get_valuation_items():
    if CART_KEY not in st.session_state:
        # Przeniesienie danych ze starej wersji szybkiej wyceny
        old_items = st.session_state.get(
            "quick_valuation_items",
            {},
        )

        st.session_state[CART_KEY] = old_items

    return st.session_state[CART_KEY]


def calculate_multiplier(
    target_diameter,
    target_height,
    base_diameter,
    base_height,
):
    return (
        (target_diameter / base_diameter) ** 2
        * (target_height / base_height)
    )


def add_recipe_item(
    recipe_id,
    base_diameter,
    base_height,
):
    items = get_valuation_items()
    item_id = uuid.uuid4().hex

    items[item_id] = {
        "item_id": item_id,
        "recipe_id": recipe_id,
        "target_diameter": float(base_diameter),
        "target_height": float(base_height),
        "automatic_multiplier": 1.0,
        "multiplier": 1.0,
        "multiplier_is_manual": False,
    }

    return item_id


def update_item_dimensions(
    item_id,
    target_diameter,
    target_height,
    base_diameter,
    base_height,
):
    items = get_valuation_items()

    automatic_multiplier = calculate_multiplier(
        target_diameter=target_diameter,
        target_height=target_height,
        base_diameter=base_diameter,
        base_height=base_height,
    )

    items[item_id].update(
        {
            "target_diameter": float(target_diameter),
            "target_height": float(target_height),
            "automatic_multiplier": automatic_multiplier,
            "multiplier": automatic_multiplier,
            "multiplier_is_manual": False,
        }
    )

    return items[item_id]


def update_item_multiplier(item_id, multiplier):
    items = get_valuation_items()

    items[item_id].update(
        {
            "multiplier": float(multiplier),
            "multiplier_is_manual": True,
        }
    )

    return items[item_id]


def remove_recipe_item(item_id):
    items = get_valuation_items()
    items.pop(item_id, None)


def clear_valuation_items():
    st.session_state[CART_KEY] = {}