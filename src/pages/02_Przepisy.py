import streamlit as st
import pandas as pd

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
                        DELETE FROM RecipeComponents
                        WHERE parent_recipe_id = ?
                           OR child_recipe_id = ?;
                        """,
                        deleted_recipe_id,
                        deleted_recipe_id,
                    )

                    cursor.execute(
                        """
                        DELETE FROM RecipeIngredients
                        WHERE recipe_id = ?;
                        """,
                        deleted_recipe_id,
                    )

                    cursor.execute(
                        """
                        DELETE FROM Recipes
                        WHERE recipe_id = ?;
                        """,
                        deleted_recipe_id,
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
# ZARZĄDZANIE SKŁADNIKAMI PRZEPISÓW
# =========================================================

st.header("Składniki przepisów")

st.caption(
    "Rozwiń przepis, edytuj tabelę, dodaj lub usuń "
    "wiersze, a następnie zapisz zmiany. "
    "Cena i wielkość opakowania dotyczą składnika "
    "we wszystkich przepisach."
)


def optional_positive_number(value, field_name):
    if value is None or pd.isna(value):
        return None

    number = float(value)

    if number <= 0:
        raise ValueError(
            f"Pole „{field_name}” musi być dodatnie."
        )

    return number


for recipe in recipes:
    recipe_id = recipe["recipe_id"]
    recipe_name = recipe["name"]

    with st.expander(
        recipe_name,
        expanded=False,
    ):
        recipe_ingredients = fetch_rows(
            """
            SELECT
                i.ingredient_id,
                i.name AS ingredient,
                ri.quantity,
                i.unit,
                i.package_price,
                i.package_quantity
            FROM RecipeIngredients AS ri

            JOIN Ingredients AS i
                ON i.ingredient_id
                    = ri.ingredient_id

            WHERE ri.recipe_id = ?

            ORDER BY i.name;
            """,
            (recipe_id,),
        )

        editor_rows = [
            {
                "ingredient_id": row["ingredient_id"],
                "ingredient": row["ingredient"],
                "quantity": float(row["quantity"]),
                "unit": row["unit"],
                "package_price": (
                    None
                    if row["package_price"] is None
                    else float(row["package_price"])
                ),
                "package_quantity": (
                    None
                    if row["package_quantity"] is None
                    else float(
                        row["package_quantity"]
                    )
                ),
            }
            for row in recipe_ingredients
        ]

        ingredient_dataframe = pd.DataFrame(
            editor_rows,
            columns=[
                "ingredient_id",
                "ingredient",
                "quantity",
                "unit",
                "package_price",
                "package_quantity",
            ],
        )
        st.info(
            "🗑️ Aby usunąć składnik, zaznacz jego wiersz "
            "klikając pole po lewej stronie tabeli, a następnie "
            "użyj klawisza Delete lub ikony usuwania. "
            "➕ Nowy składnik dodasz przyciskiem pod tabelą."
        )
        edited_dataframe = st.data_editor(
            ingredient_dataframe,
            key=f"recipe_editor_{recipe_id}",
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_order=(
                "ingredient",
                "quantity",
                "unit",
                "package_price",
                "package_quantity",
            ),
            column_config={
                "ingredient_id": None,

                "ingredient": st.column_config.TextColumn(
                    "Składnik",
                    required=True,
                    width="large",
                    help=(
                        "Wpisz istniejący lub nowy "
                        "składnik."
                    ),
                ),

                "quantity": st.column_config.NumberColumn(
                    "Ilość w przepisie",
                    required=True,
                    min_value=0.01,
                    step=1.0,
                    format="%.2f",
                ),

                "unit": st.column_config.SelectboxColumn(
                    "Jednostka",
                    options=["g", "ml", "szt"],
                    required=True,
                ),

                "package_price": (
                    st.column_config.NumberColumn(
                        "Cena opakowania",
                        min_value=0.01,
                        step=0.10,
                        format="%.2f zł",
                        help=(
                            "Może pozostać pusta."
                        ),
                    )
                ),

                "package_quantity": (
                    st.column_config.NumberColumn(
                        "Ilość w opakowaniu",
                        min_value=0.01,
                        step=1.0,
                        format="%.2f",
                        help=(
                            "Może pozostać pusta."
                        ),
                    )
                ),
            },
        )

        if st.button(
            "Zapisz składniki",
            type="primary",
            key=f"save_recipe_ingredients_{recipe_id}",
        ):
            try:
                validated_rows = []
                used_names = set()

                for row in edited_dataframe.to_dict(
                    orient="records"
                ):
                    ingredient_name = str(
                        row.get("ingredient") or ""
                    ).strip()

                    if not ingredient_name:
                        raise ValueError(
                            "Nazwa składnika nie może "
                            "być pusta."
                        )

                    normalized_name = (
                        ingredient_name.casefold()
                    )

                    if normalized_name in used_names:
                        raise ValueError(
                            f"Składnik „{ingredient_name}” "
                            "występuje w tabeli więcej "
                            "niż raz."
                        )

                    used_names.add(normalized_name)

                    quantity = optional_positive_number(
                        row.get("quantity"),
                        "Ilość w przepisie",
                    )

                    if quantity is None:
                        raise ValueError(
                            f"Podaj ilość składnika "
                            f"„{ingredient_name}”."
                        )

                    unit = str(
                        row.get("unit") or ""
                    ).strip()

                    if unit not in ("g", "ml", "szt"):
                        raise ValueError(
                            f"Nieprawidłowa jednostka dla "
                            f"„{ingredient_name}”."
                        )

                    package_price = (
                        optional_positive_number(
                            row.get("package_price"),
                            "Cena opakowania",
                        )
                    )

                    package_quantity = (
                        optional_positive_number(
                            row.get(
                                "package_quantity"
                            ),
                            "Ilość w opakowaniu",
                        )
                    )

                    ingredient_id_value = row.get(
                        "ingredient_id"
                    )

                    ingredient_id = (
                        None
                        if (
                            ingredient_id_value is None
                            or pd.isna(
                                ingredient_id_value
                            )
                        )
                        else int(ingredient_id_value)
                    )

                    validated_rows.append(
                        {
                            "ingredient_id": (
                                ingredient_id
                            ),
                            "ingredient": (
                                ingredient_name
                            ),
                            "quantity": quantity,
                            "unit": unit,
                            "package_price": (
                                package_price
                            ),
                            "package_quantity": (
                                package_quantity
                            ),
                        }
                    )

                connection = get_connection()

                try:
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        SELECT ingredient_id
                        FROM RecipeIngredients
                        WHERE recipe_id = ?;
                        """,
                        recipe_id,
                    )

                    previous_ingredient_ids = {
                        row[0]
                        for row in cursor.fetchall()
                    }

                    saved_ingredient_ids = set()

                    for row in validated_rows:
                        ingredient_id = row[
                            "ingredient_id"
                        ]

                        if ingredient_id is not None:
                            cursor.execute(
                                """
                                SELECT COUNT(*)
                                FROM Ingredients
                                WHERE name = ?
                                  AND ingredient_id <> ?;
                                """,
                                row["ingredient"],
                                ingredient_id,
                            )

                            if cursor.fetchone()[0] > 0:
                                raise ValueError(
                                    f"Inny składnik ma już "
                                    f"nazwę "
                                    f"„{row['ingredient']}”."
                                )

                            cursor.execute(
                                """
                                UPDATE Ingredients
                                SET
                                    name = ?,
                                    unit = ?,
                                    package_price = ?,
                                    package_quantity = ?,
                                    updated_at =
                                        SYSDATETIME()
                                WHERE ingredient_id = ?;
                                """,
                                row["ingredient"],
                                row["unit"],
                                row["package_price"],
                                row["package_quantity"],
                                ingredient_id,
                            )

                        else:
                            cursor.execute(
                                """
                                SELECT ingredient_id
                                FROM Ingredients
                                WHERE name = ?;
                                """,
                                row["ingredient"],
                            )

                            existing = cursor.fetchone()

                            if existing:
                                ingredient_id = existing[0]

                                cursor.execute(
                                    """
                                    UPDATE Ingredients
                                    SET
                                        unit = ?,
                                        package_price =
                                            COALESCE(
                                                ?,
                                                package_price
                                            ),
                                        package_quantity =
                                            COALESCE(
                                                ?,
                                                package_quantity
                                            ),
                                        updated_at =
                                            SYSDATETIME()
                                    WHERE ingredient_id = ?;
                                    """,
                                    row["unit"],
                                    row["package_price"],
                                    row["package_quantity"],
                                    ingredient_id,
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
                                    OUTPUT
                                        INSERTED.ingredient_id
                                    VALUES (?, ?, ?, ?);
                                    """,
                                    row["ingredient"],
                                    row["package_quantity"],
                                    row["unit"],
                                    row["package_price"],
                                )

                                ingredient_id = (
                                    cursor.fetchone()[0]
                                )

                        if (
                            ingredient_id
                            in saved_ingredient_ids
                        ):
                            raise ValueError(
                                f"Składnik "
                                f"„{row['ingredient']}” "
                                "został dodany więcej "
                                "niż raz."
                            )

                        saved_ingredient_ids.add(
                            ingredient_id
                        )

                        cursor.execute(
                            """
                            SELECT COUNT(*)
                            FROM RecipeIngredients
                            WHERE recipe_id = ?
                              AND ingredient_id = ?;
                            """,
                            recipe_id,
                            ingredient_id,
                        )

                        mapping_exists = (
                            cursor.fetchone()[0] > 0
                        )

                        if mapping_exists:
                            cursor.execute(
                                """
                                UPDATE RecipeIngredients
                                SET quantity = ?
                                WHERE recipe_id = ?
                                  AND ingredient_id = ?;
                                """,
                                row["quantity"],
                                recipe_id,
                                ingredient_id,
                            )

                        else:
                            cursor.execute(
                                """
                                INSERT INTO
                                    RecipeIngredients (
                                        recipe_id,
                                        ingredient_id,
                                        quantity
                                    )
                                VALUES (?, ?, ?);
                                """,
                                recipe_id,
                                ingredient_id,
                                row["quantity"],
                            )

                    removed_ingredient_ids = (
                        previous_ingredient_ids
                        - saved_ingredient_ids
                    )

                    for removed_ingredient_id in (
                        removed_ingredient_ids
                    ):
                        cursor.execute(
                            """
                            DELETE FROM RecipeIngredients
                            WHERE recipe_id = ?
                              AND ingredient_id = ?;
                            """,
                            recipe_id,
                            removed_ingredient_id,
                        )

                    connection.commit()

                except Exception:
                    connection.rollback()
                    raise

                finally:
                    connection.close()

                st.success(
                    f"Składniki przepisu "
                    f"„{recipe_name}” zostały zapisane."
                )
                st.rerun()

            except ValueError as error:
                st.error(str(error))

            except Exception as error:
                st.error(
                    "Nie udało się zapisać składników."
                )
                st.exception(error)

# =========================================================
# PODPRZEPISY
# =========================================================

with st.expander(
    "Podprzepisy",
    expanded=False,
):
    if len(recipes) < 2:
        st.info(
            "Potrzebujesz co najmniej dwóch przepisów."
        )

    else:
        parent_recipe_id = st.selectbox(
            "Przepis główny",
            options=list(recipe_by_id),
            format_func=lambda recipe_id: (
                recipe_by_id[recipe_id]["name"]
            ),
            key="component_parent_recipe",
        )

        child_options = [
            recipe_id
            for recipe_id in recipe_by_id
            if recipe_id != parent_recipe_id
        ]

        child_recipe_id = st.selectbox(
            "Przepis dodawany w całości",
            options=child_options,
            format_func=lambda recipe_id: (
                recipe_by_id[recipe_id]["name"]
            ),
            key="component_child_recipe",
        )

        quantity_factor = st.number_input(
            "Mnożnik przepisu",
            min_value=0.01,
            value=1.0,
            step=0.25,
            format="%.2f",
        )

        if st.button(
            "Dodaj podprzepis",
            key="add_recipe_component",
        ):
            with get_connection() as connection:
                cursor = connection.cursor()

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM RecipeComponents
                    WHERE parent_recipe_id = ?
                      AND child_recipe_id = ?;
                    """,
                    parent_recipe_id,
                    child_recipe_id,
                )

                already_added = (
                    cursor.fetchone()[0] > 0
                )

                cursor.execute(
                    """
                    WITH Descendants AS (
                        SELECT child_recipe_id
                        FROM RecipeComponents
                        WHERE parent_recipe_id = ?

                        UNION ALL

                        SELECT rc.child_recipe_id
                        FROM RecipeComponents AS rc

                        JOIN Descendants AS d
                            ON rc.parent_recipe_id
                                = d.child_recipe_id
                    )
                    SELECT COUNT(*)
                    FROM Descendants
                    WHERE child_recipe_id = ?

                    OPTION (MAXRECURSION 100);
                    """,
                    child_recipe_id,
                    parent_recipe_id,
                )

                creates_cycle = (
                    cursor.fetchone()[0] > 0
                )

                if already_added:
                    st.warning(
                        "Ten podprzepis jest już dodany."
                    )

                elif creates_cycle:
                    st.error(
                        "Nie można utworzyć cyklicznego "
                        "powiązania przepisów."
                    )

                else:
                    cursor.execute(
                        """
                        INSERT INTO RecipeComponents (
                            parent_recipe_id,
                            child_recipe_id,
                            quantity_factor
                        )
                        VALUES (?, ?, ?);
                        """,
                        parent_recipe_id,
                        child_recipe_id,
                        quantity_factor,
                    )

                    connection.commit()

                    st.success("Podprzepis został dodany.")
                    st.rerun()

        current_components = fetch_rows(
            """
            SELECT
                rc.child_recipe_id,
                r.name AS child_recipe,
                rc.quantity_factor
            FROM RecipeComponents AS rc

            JOIN Recipes AS r
                ON r.recipe_id
                    = rc.child_recipe_id

            WHERE rc.parent_recipe_id = ?

            ORDER BY r.name;
            """,
            (parent_recipe_id,),
        )

        if current_components:
            st.dataframe(
                current_components,
                use_container_width=True,
                hide_index=True,
                column_order=(
                    "child_recipe",
                    "quantity_factor",
                ),
                column_config={
                    "child_recipe": "Podprzepis",
                    "quantity_factor": "Mnożnik",
                },
            )

            component_by_id = {
                row["child_recipe_id"]: row
                for row in current_components
            }

            removed_component_id = st.selectbox(
                "Podprzepis do usunięcia",
                options=list(component_by_id),
                format_func=lambda recipe_id: (
                    component_by_id[recipe_id][
                        "child_recipe"
                    ]
                ),
                key="remove_recipe_component",
            )

            if st.button(
                "Usuń podprzepis",
                key="remove_component_button",
            ):
                with get_connection() as connection:
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        DELETE FROM RecipeComponents
                        WHERE parent_recipe_id = ?
                          AND child_recipe_id = ?;
                        """,
                        parent_recipe_id,
                        removed_component_id,
                    )

                    connection.commit()

                st.success("Podprzepis został usunięty.")
                st.rerun()

        else:
            st.info(
                "Ten przepis nie ma podprzepisów."
            )
