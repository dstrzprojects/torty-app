import pandas as pd
import streamlit as st

from db import get_connection

st.title("Składniki")

st.info(
    "Edytuj dane bezpośrednio w tabeli. "
    "➕ Nowy składnik dodasz przyciskiem pod tabelą. "
    "🗑️ Aby usunąć składnik, zaznacz wiersz po lewej stronie "
    "i użyj klawisza Delete lub ikony kosza. "
    "Na końcu kliknij „Zapisz zmiany”."
)


def fetch_ingredients():
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                ingredient_id,
                name,
                package_quantity,
                unit,
                package_price
            FROM Ingredients
            ORDER BY name;
        """)

        columns = [
            column[0]
            for column in cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def optional_positive_number(
    value,
    field_name,
    ingredient_name,
):
    if value is None or pd.isna(value):
        return None

    try:
        cleaned_value = (
            str(value)
            .replace("zł", "")
            .replace(",", ".")
            .strip()
        )

        if not cleaned_value:
            return None

        number = float(cleaned_value)

    except (TypeError, ValueError):
        raise ValueError(
            f"Składnik „{ingredient_name}”: "
            f"pole „{field_name}” nie jest liczbą. "
            f"Otrzymana wartość: {value!r}."
        )

    if number <= 0:
        raise ValueError(
            f"Składnik „{ingredient_name}”: "
            f"pole „{field_name}” musi być dodatnie. "
            f"Otrzymana wartość: {number}."
        )

    return number


ingredients = fetch_ingredients()

table_rows = [
    {
        "ingredient_id": row["ingredient_id"],
        "name": row["name"],
        "package_quantity": (
            None
            if row["package_quantity"] is None
            else float(row["package_quantity"])
        ),
        "unit": row["unit"],
        "package_price": (
            None
            if row["package_price"] is None
            else float(row["package_price"])
        ),
    }
    for row in ingredients
]

ingredients_dataframe = pd.DataFrame(
    table_rows,
    columns=[
        "ingredient_id",
        "name",
        "package_quantity",
        "unit",
        "package_price",
    ],
)

edited_dataframe = st.data_editor(
    ingredients_dataframe,
    use_container_width=True,
    hide_index=True,
    height="auto",
    num_rows="dynamic",
    key="ingredients_editor",
    column_order=(
        "ingredient_id",
        "name",
        "package_quantity",
        "unit",
        "package_price",
    ),
    column_config={
        "ingredient_id": st.column_config.NumberColumn(
            "LP",
            disabled=True,
            width="small",
            help=(
                "Numer jest nadawany automatycznie "
                "przez bazę po zapisaniu."
            ),
        ),
        "name": st.column_config.TextColumn(
            "Nazwa",
            required=True,
            width="large",
        ),
        "package_quantity": (
            st.column_config.NumberColumn(
                "Ilość w opakowaniu",
                min_value=0.01,
                step=1.0,
                format="%.2f",
                help="Może pozostać pusta.",
            )
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
                step=0.01,
                format="%.2f zł",
                help="Może pozostać pusta.",
            )
        ),
    },
)


if st.button(
    "Zapisz zmiany",
    type="primary",
    use_container_width=True,
):
    try:
        validated_rows = []
        used_names = set()

        for row in edited_dataframe.to_dict(
            orient="records"
        ):
            ingredient_id_value = row.get(
                "ingredient_id"
            )

            ingredient_id = (
                None
                if (
                    ingredient_id_value is None
                    or pd.isna(ingredient_id_value)
                )
                else int(ingredient_id_value)
            )

            name = str(
                row.get("name") or ""
            ).strip()

            # Całkowicie pusty nowy wiersz pomijamy.
            if not name and ingredient_id is None:
                continue

            if not name:
                raise ValueError(
                    "Nazwa składnika nie może być pusta."
                )

            normalized_name = name.casefold()

            if normalized_name in used_names:
                raise ValueError(
                    f"Składnik „{name}” występuje "
                    "w tabeli więcej niż raz."
                )

            used_names.add(normalized_name)

            unit = str(
                row.get("unit") or ""
            ).strip()

            if unit not in ("g", "ml", "szt"):
                raise ValueError(
                    f"Wybierz jednostkę dla składnika "
                    f"„{name}”."
                )

            package_quantity = optional_positive_number(
                row.get("package_quantity"),
                "Ilość w opakowaniu",
                name,
            )
            
            package_price = optional_positive_number(
                row.get("package_price"),
                "Cena opakowania",
                name,
            )

            validated_rows.append(
                {
                    "ingredient_id": ingredient_id,
                    "name": name,
                    "package_quantity": (
                        package_quantity
                    ),
                    "unit": unit,
                    "package_price": package_price,
                }
            )

        original_ids = {
            row["ingredient_id"]
            for row in ingredients
        }

        edited_ids = {
            row["ingredient_id"]
            for row in validated_rows
            if row["ingredient_id"] is not None
        }

        removed_ids = original_ids - edited_ids

        connection = get_connection()

        try:
            cursor = connection.cursor()

            # ---------------------------------------------
            # USUWANIE
            # ---------------------------------------------

            for removed_id in removed_ids:
                cursor.execute(
                    """
                    SELECT r.name
                    FROM RecipeIngredients AS ri

                    JOIN Recipes AS r
                        ON r.recipe_id = ri.recipe_id

                    WHERE ri.ingredient_id = ?

                    ORDER BY r.name;
                    """,
                    removed_id,
                )

                used_in_recipes = [
                    row[0]
                    for row in cursor.fetchall()
                ]

                if used_in_recipes:
                    raise ValueError(
                        "Nie można usunąć składnika, "
                        "ponieważ jest używany w przepisach: "
                        + ", ".join(used_in_recipes)
                    )

                # Zamówienie zachowuje migawkę nazwy i ceny,
                # więc odłączamy tylko identyfikator produktu.
                cursor.execute(
                    """
                    UPDATE OrderIngredients
                    SET ingredient_id = NULL
                    WHERE ingredient_id = ?;
                    """,
                    removed_id,
                )

                cursor.execute(
                    """
                    DELETE FROM Ingredients
                    WHERE ingredient_id = ?;
                    """,
                    removed_id,
                )

            # ---------------------------------------------
            # EDYCJA I DODAWANIE
            # ---------------------------------------------

            for row in validated_rows:
                ingredient_id = row["ingredient_id"]

                if ingredient_id is None:
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM Ingredients
                        WHERE name = ?;
                        """,
                        row["name"],
                    )

                    if cursor.fetchone()[0] > 0:
                        raise ValueError(
                            f"Składnik „{row['name']}” "
                            "już istnieje."
                        )

                    cursor.execute(
                        """
                        INSERT INTO Ingredients (
                            name,
                            package_quantity,
                            unit,
                            package_price
                        )
                        OUTPUT INSERTED.ingredient_id
                        VALUES (?, ?, ?, ?);
                        """,
                        row["name"],
                        row["package_quantity"],
                        row["unit"],
                        row["package_price"],
                    )
                    new_ingredient_id = cursor.fetchone()[0]
                else:
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM Ingredients
                        WHERE name = ?
                          AND ingredient_id <> ?;
                        """,
                        row["name"],
                        ingredient_id,
                    )

                    if cursor.fetchone()[0] > 0:
                        raise ValueError(
                            f"Inny składnik ma już nazwę "
                            f"„{row['name']}”."
                        )

                    cursor.execute(
                        """
                        UPDATE Ingredients
                        SET
                            name = ?,
                            package_quantity = ?,
                            unit = ?,
                            package_price = ?,
                            updated_at = SYSDATETIME()
                        WHERE ingredient_id = ?;
                        """,
                        row["name"],
                        row["package_quantity"],
                        row["unit"],
                        row["package_price"],
                        ingredient_id,
                    )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

        st.success(
            "Zmiany w składnikach zostały zapisane."
        )
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            "Nie udało się zapisać zmian w bazie."
        )
        st.exception(error)