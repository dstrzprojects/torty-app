import streamlit as st

from pricing import (
    calculate_scaled_ingredients,
    get_recipes,
)
from valuation_cart import get_valuation_items


st.title("Wycena")


# =========================================================
# PRZEPISY I WSPÓLNA LISTA POZYCJI
# =========================================================

recipes = get_recipes()

if not recipes:
    st.info("Najpierw utwórz przepis.")
    st.stop()

recipe_by_id = {
    recipe["recipe_id"]: recipe
    for recipe in recipes
}

valuation_items = get_valuation_items()

if not valuation_items:
    st.info(
        "Lista wyceny jest pusta. Dodaj przepisy "
        "w zakładce „Szybka wycena”."
    )

    st.page_link(
        "pages/06_Szybka_Wycena.py",
        label="Przejdź do szybkiej wyceny",
        icon="🧮",
    )

    st.stop()


# =========================================================
# OBLICZANIE WSZYSTKICH POZYCJI
# =========================================================

position_rows = []
ingredient_rows = []
missing_price_ingredients = set()
ingredients_cost = 0.0

recipe_occurrences = {}

for item_id, item in valuation_items.items():
    recipe_id = item["recipe_id"]

    if recipe_id not in recipe_by_id:
        continue

    recipe = recipe_by_id[recipe_id]

    recipe_occurrences[recipe_id] = (
        recipe_occurrences.get(recipe_id, 0) + 1
    )

    occurrence = recipe_occurrences[recipe_id]

    position_name = (
        f"{recipe['name']} ({occurrence})"
    )

    target_diameter = float(
        item["target_diameter"]
    )
    target_height = float(
        item["target_height"]
    )
    multiplier = float(item["multiplier"])

    pricing_result = calculate_scaled_ingredients(
        recipe_id=recipe_id,
        target_diameter=target_diameter,
        target_height=target_height,
        correction_percent=0,
        scale_factor_override=multiplier,
    )

    position_cost = float(
        pricing_result["ingredients_cost"]
    )

    ingredients_cost += position_cost

    position_rows.append(
        {
            "recipe": position_name,
            "target_diameter": target_diameter,
            "target_height": target_height,
            "multiplier": multiplier,
            "ingredients_cost": position_cost,
        }
    )

    for ingredient_row in pricing_result["ingredients"]:
        displayed_row = dict(ingredient_row)
        displayed_row["recipe"] = position_name
        ingredient_rows.append(displayed_row)

    missing_price_ingredients.update(
        pricing_result["missing_price_ingredients"]
    )


if not position_rows:
    st.warning(
        "Żaden z dodanych przepisów nie jest już dostępny."
    )
    st.stop()


# =========================================================
# POZYCJE WYCENY
# =========================================================

with st.expander("Wycena tortu", expanded=True):
    st.caption(
        "Pozycje są wspólne z zakładką „Szybka wycena”. "
        "Tam możesz zmieniać przepisy, wymiary i mnożniki."
    )

    st.dataframe(
        position_rows,
        use_container_width=True,
        hide_index=True,
        column_order=(
            "recipe",
            "target_diameter",
            "target_height",
            "multiplier",
            "ingredients_cost",
        ),
        column_config={
            "recipe": "Przepis",
            "target_diameter": st.column_config.NumberColumn(
                "Średnica",
                format="%.1f cm",
            ),
            "target_height": st.column_config.NumberColumn(
                "Wysokość",
                format="%.1f cm",
            ),
            "multiplier": st.column_config.NumberColumn(
                "Mnożnik",
                format="× %.3f",
            ),
            "ingredients_cost": (
                st.column_config.NumberColumn(
                    "Koszt składników",
                    format="%.2f zł",
                )
            ),
        },
    )

    st.metric(
        "Łączny koszt składników",
        f"{ingredients_cost:.2f} zł",
    )

    st.page_link(
        "pages/06_Szybka_Wycena.py",
        label="Zmień pozycje wyceny",
        icon="✏️",
    )

OTHER_COST_DEFAULTS = {
    "work_hours": 8.0,
    "hourly_rate": 50.0,
    "utilities_cost": 0.1*ingredients_cost,
    "depreciation_cost": 0.5,
    "decorations_cost": 0.0,
    "packaging_cost": 15.0,
}

if "valuation_other_costs" not in st.session_state:
    st.session_state.valuation_other_costs = (
        OTHER_COST_DEFAULTS.copy()
    )


def remember_other_cost(field_name):
    widget_key = f"_valuation_{field_name}"

    st.session_state.valuation_other_costs[
        field_name
    ] = float(st.session_state[widget_key])


def other_cost_input(
    label,
    field_name,
    step,
):
    widget_key = f"_valuation_{field_name}"

    if widget_key not in st.session_state:
        st.session_state[widget_key] = (
            st.session_state.valuation_other_costs.get(
                field_name,
                OTHER_COST_DEFAULTS[field_name],
            )
        )

    return st.number_input(
        label,
        min_value=0.0,
        step=step,
        key=widget_key,
        on_change=remember_other_cost,
        args=(field_name,),
    )

# =========================================================
# POZOSTAŁE KOSZTY
# =========================================================

with st.expander("Pozostałe koszty", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        work_hours = other_cost_input(
            "Czas pracy [godz.]",
            "work_hours",
            0.5,
        )

        hourly_rate = other_cost_input(
            "Stawka godzinowa [zł]",
            "hourly_rate",
            5.0,
        )

        utilities_cost = other_cost_input(
            "Media [zł]",
            "utilities_cost",
            1.0,
        )

    with col2:
        depreciation_cost = other_cost_input(
            "Amortyzacja sprzętu [zł]",
            "depreciation_cost",
            1.0,
        )

        decorations_cost = other_cost_input(
            "Dekoracje i dodatki [zł]",
            "decorations_cost",
            1.0,
        )

        packaging_cost = other_cost_input(
            "Opakowanie [zł]",
            "packaging_cost",
            1.0,
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
            + ", ".join(
                sorted(missing_price_ingredients)
            )
        )

    markup_percent = st.number_input(
        "Sugerowany narzut [%]",
        min_value=0.0,
        value=0.0,
        step=5.0,
        key="valuation_markup_percent",
    )

    suggested_price = total_cost * (
        1 + markup_percent / 100
    )

    st.metric(
        "Cena wynikająca z wyceny",
        f"{suggested_price:.2f} zł",
    )

    if "valuation_selling_price" not in st.session_state:
        st.session_state.valuation_selling_price = round(
            suggested_price,
            2,
        )

    if st.button(
        "Ustaw cenę wynikającą z wyceny",
        use_container_width=True,
    ):
        st.session_state.valuation_selling_price = round(
            suggested_price,
            2,
        )
        st.rerun()

    selling_price = st.number_input(
        "Rzeczywista cena sprzedaży [zł]",
        min_value=0.0,
        step=10.0,
        format="%.2f",
        key="valuation_selling_price",
        help=(
            "Możesz wpisać cenę uzgodnioną z klientem. "
            "Nie musi być równa wycenie."
        ),
    )

    additional_profit = selling_price - total_cost
    total_earnings = work_cost + additional_profit

    summary_col1, summary_col2 = st.columns(2)
    

    summary_col1.metric(
        "Koszt składników",
        f"{ingredients_cost:.2f} zł",
    )

    summary_col2.metric(
        "Koszty poza pracą",
        f"{cost_without_work:.2f} zł",
    )



    st.metric(
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

    st.metric(
        "Zarobek na godzinę brutto bez kosztów (PLN/h)",
        f"{total_earnings/work_hours:.2f} zł",
    )

    if selling_price < total_cost:
        st.warning(
            "Cena sprzedaży jest niższa od pełnego "
            "kosztu wykonania."
        )



# =========================================================
# SKALOWANE SKŁADNIKI
# =========================================================

with st.expander("Skalowane składniki", expanded=True):
    if missing_price_ingredients:
        st.warning(
            "Brakuje ceny lub wielkości opakowania dla: "
            + ", ".join(
                sorted(missing_price_ingredients)
            )
        )

    if not ingredient_rows:
        st.info(
            "Wybrane przepisy nie mają jeszcze składników."
        )
    else:
        st.dataframe(
            ingredient_rows,
            use_container_width=True,
            hide_index=True,
            column_order=(
                "recipe",
                "ingredient",
                "base_quantity",
                "scaled_quantity",
                "unit",
                "ingredient_cost",
            ),
            column_config={
                "recipe": "Pozycja wyceny",
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