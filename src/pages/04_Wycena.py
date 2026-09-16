import streamlit as st

from db import get_connection

st.title("Wycena tortu")


def fetch_rows(query, parameters=()):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, parameters)

        columns = [column[0] for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


recipes = fetch_rows("""
    SELECT
        recipe_id,
        name,
        base_diameter_cm,
        base_height_cm
    FROM Recipes
    ORDER BY name;
""")

if not recipes:
    st.info("Najpierw utwórz przepis.")
    st.stop()


recipe_by_id = {
    recipe["recipe_id"]: recipe
    for recipe in recipes
}

selected_recipe_id = st.selectbox(
    "Przepis",
    options=list(recipe_by_id),
    format_func=lambda recipe_id: recipe_by_id[recipe_id]["name"],
)

selected_recipe = recipe_by_id[selected_recipe_id]

base_diameter = float(selected_recipe["base_diameter_cm"])
base_height = float(selected_recipe["base_height_cm"])

st.caption(
    f"Wymiary bazowe przepisu: {base_diameter:g} × {base_height:g} cm"
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
)

scale_factor = (
    (target_diameter / base_diameter) ** 2
    * (target_height / base_height)
    * (1 + correction_percent / 100)
)

ingredient_rows = fetch_rows(
    """
    SELECT
        i.name AS ingredient,
        i.unit,

        CASE
            WHEN i.unit IN (N'szt', N'szt.')
            THEN CEILING(ri.quantity * ?)
            ELSE ROUND(ri.quantity * ?, 0)
        END AS scaled_quantity,

        ROUND(
            CASE
                WHEN i.unit IN (N'szt', N'szt.')
                THEN CEILING(ri.quantity * ?)
                ELSE ROUND(ri.quantity * ?, 0)
            END
            / i.package_quantity
            * i.package_price,
            2
        ) AS ingredient_cost

    FROM RecipeIngredients AS ri

    JOIN Ingredients AS i
        ON i.ingredient_id = ri.ingredient_id

    WHERE ri.recipe_id = ?

    ORDER BY i.name;
    """,
    (
        scale_factor,
        scale_factor,
        scale_factor,
        scale_factor,
        selected_recipe_id,
    ),
)

ingredients_cost = sum(
    float(row["ingredient_cost"])
    for row in ingredient_rows
)

st.metric("Współczynnik skalowania", f"{scale_factor:.3f}×")
st.metric("Koszt składników", f"{ingredients_cost:.2f} zł")

st.subheader("Pozostałe koszty")

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

work_cost = work_hours * hourly_rate

total_cost = (
    ingredients_cost
    + work_cost
    + utilities_cost
    + depreciation_cost
    + decorations_cost
    + packaging_cost
)

st.subheader("Cena sprzedaży")

markup_percent = st.number_input(
    "Narzut [%]",
    min_value=0.0,
    value=20.0,
    step=5.0,
)

selling_price = total_cost * (1 + markup_percent / 100)
additional_profit = selling_price - total_cost
total_earnings = work_cost + additional_profit

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

summary_col1.metric("Koszt całkowity", f"{total_cost:.2f} zł")
summary_col2.metric("Cena sprzedaży", f"{selling_price:.2f} zł")
summary_col3.metric("Wynagrodzenie za pracę", f"{work_cost:.2f} zł")
summary_col4.metric("Łącznie dla Ciebie", f"{total_earnings:.2f} zł")

st.subheader("Struktura kosztów")

st.dataframe(
    [
        {"Pozycja": "Składniki", "Koszt": ingredients_cost},
        {"Pozycja": "Robocizna", "Koszt": work_cost},
        {"Pozycja": "Media", "Koszt": utilities_cost},
        {"Pozycja": "Amortyzacja", "Koszt": depreciation_cost},
        {"Pozycja": "Dekoracje i dodatki", "Koszt": decorations_cost},
        {"Pozycja": "Opakowanie", "Koszt": packaging_cost},
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

st.subheader("Skalowane składniki")

st.dataframe(
    ingredient_rows,
    use_container_width=True,
    hide_index=True,
    column_config={
        "ingredient": "Składnik",
        "unit": "Jednostka",
        "scaled_quantity": "Ilość",
        "ingredient_cost": st.column_config.NumberColumn(
            "Koszt",
            format="%.2f zł",
        ),
    },
)