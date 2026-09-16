import streamlit as st

from db import get_connection

st.title("Skalowanie przepisu")


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

st.write(
    f"Wymiary bazowe: **{base_diameter:g} cm × {base_height:g} cm**"
)

target_diameter = st.number_input(
    "Docelowa średnica [cm]",
    min_value=1.0,
    value=base_diameter,
    step=1.0,
    key=f"diameter_{selected_recipe_id}",
)

target_height = st.number_input(
    "Docelowa wysokość [cm]",
    min_value=1.0,
    value=base_height,
    step=1.0,
    key=f"height_{selected_recipe_id}",
)

correction_percent = st.number_input(
    "Ręczna korekta ilości [%]",
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

st.metric("Współczynnik skalowania", f"{scale_factor:.3f}×")


scaled_ingredients = fetch_rows(
    """
    WITH Parameters AS (
        SELECT
            CAST(? AS DECIMAL(10,4)) AS target_diameter,
            CAST(? AS DECIMAL(10,4)) AS target_height,
            CAST(? AS DECIMAL(10,4)) AS correction_percent
    ),
    Scaled AS (
        SELECT
            i.name AS ingredient,
            i.unit,
            ri.quantity AS base_quantity,
            i.package_quantity,
            i.package_price,

            CASE
                WHEN i.unit IN (N'szt', N'szt.')
                THEN CEILING(
                    ri.quantity
                    * POWER(
                        p.target_diameter / r.base_diameter_cm,
                        2
                    )
                    * (p.target_height / r.base_height_cm)
                    * (1 + p.correction_percent / 100)
                )
                ELSE ROUND(
                    ri.quantity
                    * POWER(
                        p.target_diameter / r.base_diameter_cm,
                        2
                    )
                    * (p.target_height / r.base_height_cm)
                    * (1 + p.correction_percent / 100),
                    0
                )
            END AS scaled_quantity

        FROM RecipeIngredients AS ri

        JOIN Recipes AS r
            ON r.recipe_id = ri.recipe_id

        JOIN Ingredients AS i
            ON i.ingredient_id = ri.ingredient_id

        CROSS JOIN Parameters AS p

        WHERE r.recipe_id = ?
    )
    SELECT
        ingredient,
        base_quantity,
        scaled_quantity,
        unit,

        ROUND(
            scaled_quantity / package_quantity * package_price,
            2
        ) AS ingredient_cost,

        ROUND(
            SUM(
                scaled_quantity / package_quantity * package_price
            ) OVER (),
            2
        ) AS total_ingredients_cost

    FROM Scaled
    ORDER BY ingredient;
    """,
    (
        target_diameter,
        target_height,
        correction_percent,
        selected_recipe_id,
    ),
)

if not scaled_ingredients:
    st.info("Wybrany przepis nie ma jeszcze składników.")
else:
    total_cost = scaled_ingredients[0]["total_ingredients_cost"]

    st.metric(
        "Koszt składników",
        f"{float(total_cost):.2f} zł",
    )

    st.dataframe(
        scaled_ingredients,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ingredient": "Składnik",
            "base_quantity": "Ilość bazowa",
            "scaled_quantity": "Ilość po skalowaniu",
            "unit": "Jednostka",
            "ingredient_cost": st.column_config.NumberColumn(
                "Koszt",
                format="%.2f zł",
            ),
            "total_ingredients_cost": None,
        },
    )