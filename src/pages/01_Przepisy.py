import streamlit as st

from db import get_connection

st.title("Przepisy")


def fetch_rows(query, parameters=()):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, parameters)

        columns = [column[0] for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


st.header("Utwórz przepis")

with st.form("recipe_form", clear_on_submit=True):
    recipe_name = st.text_input("Nazwa przepisu")
    description = st.text_area("Opis")
    create_recipe = st.form_submit_button("Utwórz przepis")

if create_recipe:
    clean_name = recipe_name.strip()

    if not clean_name:
        st.error("Podaj nazwę przepisu.")
    else:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM Recipes WHERE name = ?;",
                clean_name,
            )
            already_exists = cursor.fetchone()[0] > 0

            if already_exists:
                st.warning("Przepis o takiej nazwie już istnieje.")
            else:
                cursor.execute(
                    """
                    INSERT INTO Recipes (name, description)
                    VALUES (?, ?);
                    """,
                    clean_name,
                    description.strip(),
                )
                connection.commit()
                st.success("Przepis został utworzony.")


recipes = fetch_rows("""
    SELECT recipe_id, name
    FROM Recipes
    ORDER BY name;
""")

ingredients = fetch_rows("""
    SELECT ingredient_id, name, unit
    FROM Ingredients
    ORDER BY name;
""")


st.header("Dodaj składnik do przepisu")

if not recipes:
    st.info("Najpierw utwórz przepis.")
elif not ingredients:
    st.info("Najpierw dodaj składniki.")
else:
    recipe_by_id = {
        recipe["recipe_id"]: recipe
        for recipe in recipes
    }
    ingredient_by_id = {
        ingredient["ingredient_id"]: ingredient
        for ingredient in ingredients
    }

    selected_recipe_id = st.selectbox(
        "Przepis",
        options=list(recipe_by_id),
        format_func=lambda recipe_id: recipe_by_id[recipe_id]["name"],
    )

    selected_ingredient_id = st.selectbox(
        "Składnik",
        options=list(ingredient_by_id),
        format_func=lambda ingredient_id: (
            f"{ingredient_by_id[ingredient_id]['name']} "
            f"[{ingredient_by_id[ingredient_id]['unit']}]"
        ),
    )

    selected_unit = ingredient_by_id[selected_ingredient_id]["unit"]

    with st.form("recipe_ingredient_form", clear_on_submit=True):
        quantity = st.number_input(
            f"Ilość [{selected_unit}]",
            min_value=0.01,
            step=1.0,
        )
        add_ingredient = st.form_submit_button("Dodaj do przepisu")

    if add_ingredient:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM RecipeIngredients
                WHERE recipe_id = ?
                  AND ingredient_id = ?;
                """,
                selected_recipe_id,
                selected_ingredient_id,
            )
            already_added = cursor.fetchone()[0] > 0

            if already_added:
                st.warning("Ten składnik jest już w przepisie.")
            else:
                cursor.execute(
                    """
                    INSERT INTO RecipeIngredients
                        (recipe_id, ingredient_id, quantity)
                    VALUES (?, ?, ?);
                    """,
                    selected_recipe_id,
                    selected_ingredient_id,
                    quantity,
                )
                connection.commit()
                st.success("Składnik został dodany do przepisu.")



recipe_ingredients = fetch_rows("""
    SELECT
        r.name AS recipe,
        i.name AS ingredient,
        ri.quantity,
        i.unit,

        ROUND(
            ri.quantity / i.package_quantity
            * i.package_price,
            2
        ) AS ingredient_cost,

        ROUND(
            SUM(
                ri.quantity / i.package_quantity
                * i.package_price
            ) OVER (PARTITION BY r.recipe_id),
            2
        ) AS total_ingredients_cost

    FROM RecipeIngredients AS ri

    JOIN Recipes AS r
        ON r.recipe_id = ri.recipe_id

    JOIN Ingredients AS i
        ON i.ingredient_id = ri.ingredient_id

    ORDER BY r.name, i.name;
""")

st.header("Lista składników")

st.dataframe(
    recipe_ingredients,
    use_container_width=True,
    hide_index=True,
    column_config={
        "recipe": "Przepis",
        "ingredient": "Składnik",
        "quantity": "Ilość",
        "unit": "Jednostka",
        "ingredient_cost": st.column_config.NumberColumn(
            "Koszt składnika",
            format="%.2f zł",
        ),
        "total_ingredients_cost": st.column_config.NumberColumn(
            "Łączny koszt składników",
            format="%.2f zł",
        ),
    },
)