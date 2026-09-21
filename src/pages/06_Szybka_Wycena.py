import streamlit as st

from pricing import (
    calculate_scaled_ingredients,
    get_recipes,
)

st.title("Szybka wycena")

st.caption(
    "Zaznacz przepisy, które chcesz uwzględnić. "
    "Każdy zaznaczony przepis jest liczony jeden raz "
    "według jego wymiarów bazowych."
)

recipes = get_recipes()

if not recipes:
    st.info("Nie ma jeszcze żadnych przepisów.")
    st.stop()


# =========================================================
# ZAZNACZANIE
# =========================================================

button_col1, button_col2 = st.columns(2)

with button_col1:
    if st.button(
        "Zaznacz wszystkie",
        use_container_width=True,
    ):
        for recipe in recipes:
            st.session_state[
                f"quick_recipe_{recipe['recipe_id']}"
            ] = True

        st.rerun()

with button_col2:
    if st.button(
        "Wyczyść zaznaczenie",
        use_container_width=True,
    ):
        for recipe in recipes:
            st.session_state[
                f"quick_recipe_{recipe['recipe_id']}"
            ] = False

        st.rerun()


if "quick_selected_recipes" not in st.session_state:
    st.session_state.quick_selected_recipes = {}

if "quick_recipe_multipliers" not in st.session_state:
    st.session_state.quick_recipe_multipliers = {}


def remember_recipe_selection(recipe_id):
    widget_key = f"_quick_recipe_{recipe_id}"

    st.session_state.quick_selected_recipes[recipe_id] = (
        st.session_state[widget_key]
    )


def remember_recipe_multiplier(recipe_id):
    widget_key = f"_quick_multiplier_{recipe_id}"

    st.session_state.quick_recipe_multipliers[recipe_id] = (
        st.session_state[widget_key]
    )

st.subheader("Przepisy")

header_col1, header_col2 = st.columns([4, 1])

header_col1.caption("Przepis")
header_col2.caption("Mnożnik")

selected_recipes = []

for recipe in recipes:
    recipe_id = recipe["recipe_id"]

    checkbox_key = f"_quick_recipe_{recipe_id}"
    multiplier_key = f"_quick_multiplier_{recipe_id}"

    if checkbox_key not in st.session_state:
        st.session_state[checkbox_key] = (
            st.session_state.quick_selected_recipes.get(
                recipe_id,
                False,
            )
        )

    if multiplier_key not in st.session_state:
        st.session_state[multiplier_key] = (
            st.session_state.quick_recipe_multipliers.get(
                recipe_id,
                1.0,
            )
        )

    recipe_col, multiplier_col = st.columns(
        [4, 1],
        vertical_alignment="center",
    )

    with recipe_col:
        selected = st.checkbox(
            recipe["name"],
            key=checkbox_key,
            help=(
                "Wymiary bazowe: "
                f"{float(recipe['base_diameter_cm']):g} × "
                f"{float(recipe['base_height_cm']):g} cm"
            ),
            on_change=remember_recipe_selection,
            args=(recipe_id,),
        )

    with multiplier_col:
        multiplier = st.number_input(
            "Mnożnik",
            min_value=0.25,
            value=None,
            step=0.25,
            key=multiplier_key,
            disabled=not selected,
            label_visibility="collapsed",
            on_change=remember_recipe_multiplier,
            args=(recipe_id,),
        )

    if selected:
        selected_recipes.append(
            {
                "recipe": recipe,
                "multiplier": multiplier,
            }
        )


# =========================================================
# OBLICZENIA
# =========================================================

st.divider()

if not selected_recipes:
    st.info("Zaznacz co najmniej jeden przepis.")
    st.stop()

valuation_rows = []
total_cost = 0.0
all_missing_prices = []

for selected_item in selected_recipes:
    recipe = selected_item["recipe"]
    multiplier = float(
        selected_item["multiplier"]
    )
    result = calculate_scaled_ingredients(
        recipe_id=recipe["recipe_id"],
        target_diameter=float(
            recipe["base_diameter_cm"]
        ),
        target_height=float(
            recipe["base_height_cm"]
        ),
        correction_percent=0,
    )

    base_recipe_cost = float(
        result["ingredients_cost"]
    )

    recipe_cost = (
        base_recipe_cost * multiplier
    )

    missing_prices = result[
        "missing_price_ingredients"
    ]

    total_cost += recipe_cost

    valuation_rows.append(
        {
            "recipe": recipe["name"],
            "multiplier": multiplier,
            "diameter": float(
                recipe["base_diameter_cm"]
            ),
            "height": float(
                recipe["base_height_cm"]
            ),
            "base_cost": base_recipe_cost,
            "ingredients_cost": recipe_cost,
            "valuation_status": (
                "Niepełna"
                if missing_prices
                else "Kompletna"
            ),
        }
    )

    for ingredient_name in missing_prices:
        all_missing_prices.append(
            f"{recipe['name']}: {ingredient_name}"
        )


# =========================================================
# WYNIK
# =========================================================

if all_missing_prices:
    st.metric(
        "Znany koszt zaznaczonych przepisów",
        f"{total_cost:.2f} zł",
    )

    st.warning(
        "Wycena jest niepełna. Brakuje ceny lub "
        "wielkości opakowania dla:\n\n- "
        + "\n- ".join(all_missing_prices)
    )

else:
    st.metric(
        "Łączny koszt zaznaczonych przepisów",
        f"{total_cost:.2f} zł",
    )


st.dataframe(
    valuation_rows,
    use_container_width=True,
    hide_index=True,
    column_order=(
        "recipe",
        "multiplier",
        "diameter",
        "height",
        "base_cost",
        "ingredients_cost",
        "valuation_status",
    ),
    column_config={
        "recipe": "Przepis",

        "multiplier": st.column_config.NumberColumn(
            "Mnożnik",
            format="× %.2f",
        ),

        "diameter": st.column_config.NumberColumn(
            "Średnica",
            format="%.1f cm",
        ),

        "height": st.column_config.NumberColumn(
            "Wysokość",
            format="%.1f cm",
        ),

        "base_cost": st.column_config.NumberColumn(
            "Koszt ×1",
            format="%.2f zł",
        ),

        "ingredients_cost": (
            st.column_config.NumberColumn(
                "Koszt po przemnożeniu",
                format="%.2f zł",
            )
        ),

        "valuation_status": "Stan wyceny",
    },
)