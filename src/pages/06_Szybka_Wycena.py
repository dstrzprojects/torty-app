import streamlit as st
from valuation_cart import (
    add_recipe_item,
    get_valuation_items,
    remove_recipe_item,
    update_item_dimensions,
    update_item_multiplier,
)


from pricing import (
    calculate_scaled_ingredients,
    get_recipes,
)

st.title("Szybka wycena")



recipes = get_recipes()

if not recipes:
    st.info("Nie ma jeszcze żadnych przepisów.")
    st.stop()




valuation_items = get_valuation_items()

recipe_by_id = {
    recipe["recipe_id"]: recipe
    for recipe in recipes
}

def update_quick_dimensions(
    item_id,
    base_diameter,
    base_height,
):
    diameter_key = f"_quick_diameter_{item_id}"
    height_key = f"_quick_height_{item_id}"
    multiplier_key = f"_quick_multiplier_{item_id}"

    updated_item = update_item_dimensions(
        item_id=item_id,
        target_diameter=float(
            st.session_state[diameter_key]
        ),
        target_height=float(
            st.session_state[height_key]
        ),
        base_diameter=base_diameter,
        base_height=base_height,
    )

    st.session_state[multiplier_key] = updated_item[
        "multiplier"
    ]


def update_quick_multiplier(item_id):
    multiplier_key = f"_quick_multiplier_{item_id}"

    update_item_multiplier(
        item_id=item_id,
        multiplier=float(
            st.session_state[multiplier_key]
        ),
    )



# =========================================================
# Dodawanie przepisów do wyceny
# =========================================================









st.subheader("Dodaj przepis do wyceny")

add_col1, add_col2 = st.columns(
    [5, 1],
    vertical_alignment="bottom",
)

with add_col1:
    recipe_to_add = st.selectbox(
        "Przepis",
        options=[None] + list(recipe_by_id),
        format_func=lambda recipe_id: (
            "Wybierz przepis"
            if recipe_id is None
            else recipe_by_id[recipe_id]["name"]
        ),
        key="quick_recipe_to_add",
    )

with add_col2:
    add_recipe = st.button(
        "Dodaj",
        use_container_width=True,
        disabled=recipe_to_add is None,
    )

if add_recipe:
    recipe = recipe_by_id[recipe_to_add]

    add_recipe_item(
        recipe_id=recipe_to_add,
        base_diameter=float(recipe["base_diameter_cm"]),
        base_height=float(recipe["base_height_cm"]),
    )

    st.rerun()


st.subheader("Wybrane przepisy")

selected_recipes = []
recipe_occurrences = {}

if not valuation_items:
    st.info("Dodaj przepis z listy powyżej.")


for item_id in list(
    valuation_items
):
    item = valuation_items[item_id]
    recipe_id = item["recipe_id"]

    if recipe_id not in recipe_by_id:
        remove_recipe_item(item_id)
        continue

    recipe = recipe_by_id[recipe_id]

    recipe_occurrences[recipe_id] = (
        recipe_occurrences.get(recipe_id, 0) + 1
    )
    occurrence = recipe_occurrences[recipe_id]

    base_diameter = float(recipe["base_diameter_cm"])
    base_height = float(recipe["base_height_cm"])

    diameter_key = f"_quick_diameter_{item_id}"
    height_key = f"_quick_height_{item_id}"
    multiplier_key = f"_quick_multiplier_{item_id}"

    if diameter_key not in st.session_state:
        st.session_state[diameter_key] = item[
            "target_diameter"
        ]

    if height_key not in st.session_state:
        st.session_state[height_key] = item[
            "target_height"
        ]

    if multiplier_key not in st.session_state:
        st.session_state[multiplier_key] = item[
            "multiplier"
        ]

    with st.container(border=True):
        title_col, delete_col = st.columns(
            [8, 1],
            vertical_alignment="center",
        )

        title_col.markdown(
            f"### {recipe['name']} ({occurrence})"
        )

        if delete_col.button(
            "🗑️",
            key=f"remove_quick_recipe_{item_id}",
            help="Usuń tę pozycję z wyceny",
            use_container_width=True,
        ):
            remove_recipe_item(item_id)

            for widget_key in (
                diameter_key,
                height_key,
                multiplier_key,
            ):
                st.session_state.pop(widget_key, None)

            st.rerun()

        st.caption(
            f"Wymiary bazowe: "
            f"{base_diameter:g} × {base_height:g} cm"
        )

        diameter_col, height_col, multiplier_col = (
            st.columns(3)
        )

        with diameter_col:
            target_diameter = st.number_input(
                "Średnica [cm]",
                min_value=1.0,
                step=1.0,
                key=diameter_key,
                on_change=update_quick_dimensions,
                args=(
                    item_id,
                    base_diameter,
                    base_height,
                ),
            )

        with height_col:
            target_height = st.number_input(
                "Wysokość [cm]",
                min_value=1.0,
                step=1.0,
                key=height_key,
                on_change=update_quick_dimensions,
                args=(
                    item_id,
                    base_diameter,
                    base_height,
                ),
            )

        with multiplier_col:
            multiplier = st.number_input(
                "Mnożnik",
                min_value=0.01,
                step=0.05,
                format="%.3f",
                key=multiplier_key,
                on_change=update_quick_multiplier,
                args=(item_id,),
            )

        selected_recipes.append(
            {
                "recipe": recipe,
                "multiplier": float(multiplier),
                "target_diameter": float(target_diameter),
                "target_height": float(target_height),
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
    target_diameter = float(
        selected_item["target_diameter"]
    )
    target_height = float(
        selected_item["target_height"]
    )

    base_result = calculate_scaled_ingredients(
        recipe_id=recipe["recipe_id"],
        target_diameter=float(
            recipe["base_diameter_cm"]
        ),
        target_height=float(
            recipe["base_height_cm"]
        ),
        correction_percent=0,
    )
    
    result = calculate_scaled_ingredients(
        recipe_id=recipe["recipe_id"],
        target_diameter=target_diameter,
        target_height=target_height,
        correction_percent=0,
        scale_factor_override=multiplier,
    )
    
    base_recipe_cost = float(
        base_result["ingredients_cost"]
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
            "multiplier": multiplier,
            "diameter": target_diameter,
            "height": target_height,
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