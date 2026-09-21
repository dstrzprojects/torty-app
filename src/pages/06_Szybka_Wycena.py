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


st.subheader("Przepisy")

checkbox_columns = st.columns(3)

selected_recipes = []

for index, recipe in enumerate(recipes):
    column = checkbox_columns[
        index % len(checkbox_columns)
    ]

    with column:
        selected = st.checkbox(
            recipe["name"],
            key=f"quick_recipe_{recipe['recipe_id']}",
            help=(
                f"Wymiary bazowe: "
                f"{float(recipe['base_diameter_cm']):g} × "
                f"{float(recipe['base_height_cm']):g} cm"
            ),
        )

    if selected:
        selected_recipes.append(recipe)


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

for recipe in selected_recipes:
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

    recipe_cost = float(
        result["ingredients_cost"]
    )

    missing_prices = result[
        "missing_price_ingredients"
    ]

    total_cost += recipe_cost

    valuation_rows.append(
        {
            "recipe": recipe["name"],
            "diameter": float(
                recipe["base_diameter_cm"]
            ),
            "height": float(
                recipe["base_height_cm"]
            ),
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
        "diameter",
        "height",
        "ingredients_cost",
        "valuation_status",
    ),
    column_config={
        "recipe": "Przepis",
        "diameter": st.column_config.NumberColumn(
            "Średnica",
            format="%.1f cm",
        ),
        "height": st.column_config.NumberColumn(
            "Wysokość",
            format="%.1f cm",
        ),
        "ingredients_cost": (
            st.column_config.NumberColumn(
                "Koszt składników",
                format="%.2f zł",
            )
        ),
        "valuation_status": "Stan wyceny",
    },
)