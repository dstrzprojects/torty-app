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


# =========================================================
# TWORZENIE PRZEPISU
# =========================================================

with st.expander("Utwórz przepis", expanded=False):

    with st.form("recipe_form", clear_on_submit=True):
        recipe_name = st.text_input("Nazwa przepisu")

        description = st.text_area("Opis")

        base_diameter = st.number_input(
            "Średnica bazowa [cm]",
            min_value=1.0,
            value=24.0,
            step=1.0,
        )

        base_height = st.number_input(
            "Wysokość bazowa [cm]",
            min_value=1.0,
            value=10.0,
            step=1.0,
        )

        create_recipe = st.form_submit_button("Utwórz przepis")

    if create_recipe:
        clean_name = recipe_name.strip()

        if not clean_name:
            st.error("Podaj nazwę przepisu.")
        else:
            with get_connection() as connection:
                cursor = connection.cursor()

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM Recipes
                    WHERE name = ?;
                    """,
                    clean_name,
                )

                already_exists = cursor.fetchone()[0] > 0

                if already_exists:
                    st.warning("Przepis o takiej nazwie już istnieje.")
                else:
                    cursor.execute(
                        """
                        INSERT INTO Recipes (
                            name,
                            description,
                            base_diameter_cm,
                            base_height_cm
                        )
                        VALUES (?, ?, ?, ?);
                        """,
                        clean_name,
                        description.strip(),
                        base_diameter,
                        base_height,
                    )

                    connection.commit()

                    st.success("Przepis został utworzony.")
                    st.rerun()


# =========================================================
# POBIERANIE DANYCH
# =========================================================

recipes = fetch_rows("""
    SELECT
        recipe_id,
        name,
        description,
        base_diameter_cm,
        base_height_cm
    FROM Recipes
    ORDER BY name;
""")

ingredients = fetch_rows("""
    SELECT
        ingredient_id,
        name,
        unit
    FROM Ingredients
    ORDER BY name;
""")

recipe_by_id = {
    recipe["recipe_id"]: recipe
    for recipe in recipes
}

ingredient_by_id = {
    ingredient["ingredient_id"]: ingredient
    for ingredient in ingredients
}


# =========================================================
# EDYCJA PRZEPISU
# =========================================================


with st.expander("Edytuj przepis", expanded=False):
    if not recipes:
        st.info("Nie ma jeszcze żadnych przepisów.")
    else:
        edited_recipe_id = st.selectbox(
            "Wybierz przepis do edycji",
            options=list(recipe_by_id),
            format_func=lambda recipe_id: recipe_by_id[recipe_id]["name"],
            key="edit_recipe",
        )

        edited_recipe = recipe_by_id[edited_recipe_id]

        with st.form("edit_recipe_form"):
            edited_name = st.text_input(
                "Nazwa przepisu",
                value=edited_recipe["name"],
            )

            edited_description = st.text_area(
                "Opis przepisu",
                value=edited_recipe["description"] or "",
            )

            edited_diameter = st.number_input(
                "Średnica bazowa [cm]",
                min_value=1.0,
                value=float(edited_recipe["base_diameter_cm"]),
                step=1.0,
            )

            edited_height = st.number_input(
                "Wysokość bazowa [cm]",
                min_value=1.0,
                value=float(edited_recipe["base_height_cm"]),
                step=1.0,
            )

            save_recipe = st.form_submit_button("Zapisz zmiany")

        if save_recipe:
            clean_name = edited_name.strip()

            if not clean_name:
                st.error("Nazwa przepisu nie może być pusta.")
            else:
                with get_connection() as connection:
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM Recipes
                        WHERE name = ?
                          AND recipe_id <> ?;
                        """,
                        clean_name,
                        edited_recipe_id,
                    )

                    name_taken = cursor.fetchone()[0] > 0

                    if name_taken:
                        st.warning("Inny przepis ma już taką nazwę.")
                    else:
                        cursor.execute(
                            """
                            UPDATE Recipes
                            SET
                                name = ?,
                                description = ?,
                                base_diameter_cm = ?,
                                base_height_cm = ?
                            WHERE recipe_id = ?;
                            """,
                            clean_name,
                            edited_description.strip(),
                            edited_diameter,
                            edited_height,
                            edited_recipe_id,
                        )

                        connection.commit()

                        st.success("Przepis został zaktualizowany.")
                        st.rerun()


    # =====================================================
    # USUWANIE PRZEPISU
    # =====================================================

    
    with st.expander("Usuń przepis", expanded=False):
        confirm_delete = st.checkbox(
            f"Potwierdzam usunięcie przepisu: "
            f"{edited_recipe['name']}",
            key=f"confirm_delete_{edited_recipe_id}",
        )

        if st.button(
            "Usuń przepis",
            disabled=not confirm_delete,
            type="primary",
            key=f"delete_recipe_{edited_recipe_id}",
        ):
            try:
                with get_connection() as connection:
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        DELETE FROM RecipeIngredients
                        WHERE recipe_id = ?;
                        """,
                        edited_recipe_id,
                    )

                    cursor.execute(
                        """
                        DELETE FROM Recipes
                        WHERE recipe_id = ?;
                        """,
                        edited_recipe_id,
                    )

                    connection.commit()

                st.success("Przepis został usunięty.")
                st.rerun()

            except Exception as error:
                st.error(
                    "Nie udało się usunąć przepisu. "
                    "Może być powiązany z innymi danymi."
                )
                st.exception(error)

# =========================================================
# DODAWANIE SKŁADNIKA DO PRZEPISU
# =========================================================

with st.expander(
    "Dodaj składnik do przepisu",
    expanded=False,
):

    st.subheader("Nie ma składnika na liście?")

    with st.form("quick_ingredient_form", clear_on_submit=True):
        new_ingredient_name = st.text_input(
            "Nazwa nowego składnika"
        )

        new_ingredient_unit = st.selectbox(
            "Jednostka nowego składnika",
            ["g", "ml", "szt"],
        )

        create_ingredient = st.form_submit_button(
            "Dodaj składnik do ogólnej bazy"
        )

    if create_ingredient:
        clean_ingredient_name = new_ingredient_name.strip()

        if not clean_ingredient_name:
            st.error("Podaj nazwę składnika.")
        else:
            with get_connection() as connection:
                cursor = connection.cursor()

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM Ingredients
                    WHERE name = ?;
                    """,
                    clean_ingredient_name,
                )

                ingredient_exists = cursor.fetchone()[0] > 0

                if ingredient_exists:
                    st.warning(
                        "Składnik o takiej nazwie już istnieje."
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO Ingredients (
                            name,
                            package_quantity,
                            unit,
                            package_price
                        )
                        VALUES (?, NULL, ?, NULL);
                        """,
                        clean_ingredient_name,
                        new_ingredient_unit,
                    )

                    connection.commit()

                    st.success(
                        "Składnik został dodany do ogólnej bazy "
                        "bez danych o cenie."
                    )
                    st.rerun()


    st.subheader("Przypisz składnik do przepisu")

    if not recipes:
        st.info("Najpierw utwórz przepis.")

    elif not ingredients:
        st.info("Dodaj pierwszy składnik powyżej.")

    else:
        selected_recipe_id = st.selectbox(
            "Przepis",
            options=list(recipe_by_id),
            format_func=lambda recipe_id: (
                recipe_by_id[recipe_id]["name"]
            ),
            key="add_ingredient_recipe",
        )

        selected_ingredient_id = st.selectbox(
            "Składnik",
            options=list(ingredient_by_id),
            format_func=lambda ingredient_id: (
                f"{ingredient_by_id[ingredient_id]['name']} "
                f"[{ingredient_by_id[ingredient_id]['unit']}]"
            ),
            key="add_ingredient",
        )

        selected_unit = ingredient_by_id[
            selected_ingredient_id
        ]["unit"]

        with st.form(
            "recipe_ingredient_form",
            clear_on_submit=True,
        ):
            quantity = st.number_input(
                f"Ilość [{selected_unit}]",
                min_value=0.01,
                value=1.0,
                step=1.0,
            )

            add_ingredient = st.form_submit_button(
                "Dodaj do przepisu"
            )

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
                    st.warning(
                        "Ten składnik jest już przypisany "
                        "do wybranego przepisu."
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO RecipeIngredients (
                            recipe_id,
                            ingredient_id,
                            quantity
                        )
                        VALUES (?, ?, ?);
                        """,
                        selected_recipe_id,
                        selected_ingredient_id,
                        quantity,
                    )

                    connection.commit()

                    st.success(
                        "Składnik został dodany do przepisu."
                    )
                    st.rerun()


# =========================================================
# LISTA SKŁADNIKÓW WYBRANEGO PRZEPISU
# =========================================================
with st.expander("Lista składników", expanded=True):
    if not recipes:
        st.info("Brak przepisów.")
    else:
        filtered_recipe_id = st.selectbox(
            "Wyszukaj przepis",
            options=list(recipe_by_id),
            format_func=lambda recipe_id: recipe_by_id[recipe_id]["name"],
            key="ingredient_list_recipe",
        )

        recipe_ingredients = fetch_rows(
            """
            SELECT
                i.name AS ingredient,
                ri.quantity,
                i.unit,

                CASE
                    WHEN i.package_quantity IS NULL
                      OR i.package_price IS NULL
                    THEN NULL
                    ELSE ROUND(
                        ri.quantity
                        / NULLIF(i.package_quantity, 0)
                        * i.package_price,
                        2
                    )
                END AS ingredient_cost

            FROM RecipeIngredients AS ri

            JOIN Ingredients AS i
                ON i.ingredient_id = ri.ingredient_id

            WHERE ri.recipe_id = ?

            ORDER BY i.name;
            """,
            (filtered_recipe_id,),
        )

        known_costs = [
            float(row["ingredient_cost"])
            for row in recipe_ingredients
            if row["ingredient_cost"] is not None
        ]

        missing_prices = [
            row["ingredient"]
            for row in recipe_ingredients
            if row["ingredient_cost"] is None
        ]

        total_ingredients_cost = sum(known_costs)

        st.metric(
            "Znany koszt składników",
            f"{total_ingredients_cost:.2f} zł",
        )

        if missing_prices:
            st.warning(
                "Wycena jest niepełna. Brak ceny dla: "
                + ", ".join(missing_prices)
            )

        if not recipe_ingredients:
            st.info("Wybrany przepis nie ma jeszcze składników.")
        else:
            st.dataframe(
                recipe_ingredients,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ingredient": "Składnik",
                    "quantity": "Ilość",
                    "unit": "Jednostka",
                    "ingredient_cost": st.column_config.NumberColumn(
                        "Koszt składnika",
                        format="%.2f zł",
                    ),
                },
            )
