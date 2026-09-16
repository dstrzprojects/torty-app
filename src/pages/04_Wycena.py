import streamlit as st

from pricing import (
    calculate_scaled_ingredients,
    get_recipes,
)

st.title("Wycena")


# =========================================================
# POBIERANIE PRZEPISÓW
# =========================================================

recipes = get_recipes()

if not recipes:
    st.info("Najpierw utwórz przepis.")
    st.stop()

recipe_by_id = {
    recipe["recipe_id"]: recipe
    for recipe in recipes
}


# =========================================================
# WYBÓR TORTU I SKALOWANIE
# =========================================================

with st.expander("Wycena tortu", expanded=True):
    selected_recipe_id = st.selectbox(
        "Przepis",
        options=list(recipe_by_id),
        format_func=lambda recipe_id: (
            recipe_by_id[recipe_id]["name"]
        ),
        key="valuation_recipe",
    )

    selected_recipe = recipe_by_id[selected_recipe_id]

    base_diameter = float(
        selected_recipe["base_diameter_cm"]
    )

    base_height = float(
        selected_recipe["base_height_cm"]
    )

    st.caption(
        f"Wymiary bazowe przepisu: "
        f"{base_diameter:g} × {base_height:g} cm"
    )

    target_diameter = st.number_input(
        "Średnica tortu [cm]",
        min_value=1.0,
        value=base_diameter,
        step=1.0,
        key=f"valuation_diameter_{selected_recipe_id}",
    )

    target_height = st.number_input(
        "Wysokość tortu [cm]",
        min_value=1.0,
        value=base_height,
        step=1.0,
        key=f"valuation_height_{selected_recipe_id}",
    )

    correction_percent = st.number_input(
        "Korekta ilości składników [%]",
        min_value=-50.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
        key=f"valuation_correction_{selected_recipe_id}",
    )


# =========================================================
# WSPÓLNE OBLICZENIE SKŁADNIKÓW
# =========================================================

pricing_result = calculate_scaled_ingredients(
    recipe_id=selected_recipe_id,
    target_diameter=target_diameter,
    target_height=target_height,
    correction_percent=correction_percent,
)

scale_factor = pricing_result["scale_factor"]
ingredient_rows = pricing_result["ingredients"]
ingredients_cost = pricing_result["ingredients_cost"]

missing_price_ingredients = pricing_result[
    "missing_price_ingredients"
]

with st.expander("Współczynnik skalowania", expanded=False):
    st.metric(
        "Współczynnik",
        f"{scale_factor:.3f}×",
    )

    st.caption(
        "Współczynnik jest stosowany do ilości składników. "
        "Koszt jest następnie liczony od przeskalowanej ilości."
    )


# =========================================================
# POZOSTAŁE KOSZTY
# =========================================================

with st.expander("Pozostałe koszty", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        work_hours = st.number_input(
            "Czas pracy [godz.]",
            min_value=0.0,
            value=4.0,
            step=0.5,
        )

        hourly_rate = st.number_input(
            "Stawka godzinowa [zł]",
            min_value=0.0,
            value=30.0,
            step=5.0,
        )

        utilities_cost = st.number_input(
            "Media [zł]",
            min_value=0.0,
            value=10.0,
            step=1.0,
        )

    with col2:
        depreciation_cost = st.number_input(
            "Amortyzacja sprzętu [zł]",
            min_value=0.0,
            value=5.0,
            step=1.0,
        )

        decorations_cost = st.number_input(
            "Dekoracje i dodatki [zł]",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )

        packaging_cost = st.number_input(
            "Opakowanie [zł]",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )


# =========================================================
# OBLICZENIA KOŃCOWE
# =========================================================

work_cost = work_hours * hourly_rate

cost_without_work = (
    ingredients_cost
    + utilities_cost
    + depreciation_cost
    + decorations_cost
    + packaging_cost
)

total_cost = cost_without_work + work_cost


# =========================================================
# CENA SPRZEDAŻY
# =========================================================

with st.expander("Cena sprzedaży", expanded=True):
    if missing_price_ingredients:
        st.warning(
            "Wycena jest niepełna. Brakuje ceny lub "
            "wielkości opakowania dla: "
            + ", ".join(missing_price_ingredients)
        )

    markup_percent = st.number_input(
        "Sugerowany narzut [%]",
        min_value=0.0,
        value=0.0,
        step=5.0,
    )

    suggested_price = total_cost * (
        1 + markup_percent / 100
    )

    st.metric(
        "Cena wynikająca z wyceny",
        f"{suggested_price:.2f} zł",
    )

    selling_price = st.number_input(
        "Rzeczywista cena sprzedaży [zł]",
        min_value=0.0,
        value=float(round(suggested_price, 2)),
        step=10.0,
        format="%.2f",
        help=(
            "Możesz wpisać cenę uzgodnioną z klientem. "
            "Nie musi być równa wycenie."
        ),
    )

    additional_profit = selling_price - total_cost
    total_earnings = work_cost + additional_profit

    summary_col1, summary_col2 = st.columns(2)
    summary_col3, summary_col4 = st.columns(2)

    summary_col1.metric(
        "Koszt składników",
        f"{ingredients_cost:.2f} zł",
    )

    summary_col2.metric(
        "Koszty poza pracą",
        f"{cost_without_work:.2f} zł",
    )

    summary_col3.metric(
        "Wynagrodzenie za pracę",
        f"{work_cost:.2f} zł",
    )

    summary_col4.metric(
        "Cena sprzedaży",
        f"{selling_price:.2f} zł",
        delta=(
            f"{selling_price - suggested_price:+.2f} zł "
            "względem wyceny"
        ),
    )

    st.metric(
        "Łącznie dla Ciebie",
        f"{total_earnings:.2f} zł",
    )

    if selling_price < total_cost:
        st.warning(
            "Cena sprzedaży jest niższa od pełnego "
            "kosztu wykonania tortu."
        )


# =========================================================
# STRUKTURA KOSZTÓW
# =========================================================

with st.expander("Struktura kosztów", expanded=False):
    st.dataframe(
        [
            {
                "Pozycja": "Składniki",
                "Koszt": ingredients_cost,
            },
            {
                "Pozycja": "Robocizna",
                "Koszt": work_cost,
            },
            {
                "Pozycja": "Media",
                "Koszt": utilities_cost,
            },
            {
                "Pozycja": "Amortyzacja",
                "Koszt": depreciation_cost,
            },
            {
                "Pozycja": "Dekoracje i dodatki",
                "Koszt": decorations_cost,
            },
            {
                "Pozycja": "Opakowanie",
                "Koszt": packaging_cost,
            },
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Koszt": st.column_config.NumberColumn(
                "Koszt",
                format="%.2f zł",
            ),
        },
    )


# =========================================================
# SKALOWANE SKŁADNIKI
# =========================================================

with st.expander("Skalowane składniki", expanded=True):
    if not ingredient_rows:
        st.info(
            "Wybrany przepis nie ma jeszcze składników."
        )

    else:
        if missing_price_ingredients:
            st.warning(
                "Brakuje ceny lub wielkości opakowania dla: "
                + ", ".join(missing_price_ingredients)
            )

        st.dataframe(
            ingredient_rows,
            use_container_width=True,
            hide_index=True,
            column_order=(
                "ingredient",
                "base_quantity",
                "scaled_quantity",
                "unit",
                "ingredient_cost",
            ),
            column_config={
                "ingredient": "Składnik",
                "base_quantity": "Ilość bazowa",
                "scaled_quantity": "Ilość",
                "unit": "Jednostka",
                "ingredient_cost": (
                    st.column_config.NumberColumn(
                        "Koszt",
                        format="%.2f zł",
                    )
                ),
            },
        )