import streamlit as st

from db import get_connection

st.title("Składniki")


# =========================================================
# DODAWANIE SKŁADNIKA
# =========================================================

with st.expander("Dodaj składnik", expanded=False):
    with st.form("ingredient_form", clear_on_submit=True):
        name = st.text_input("Nazwa składnika")

        package_quantity = st.number_input(
            "Ilość w opakowaniu",
            min_value=0.01,
            step=1.0,
        )

        unit = st.selectbox(
            "Jednostka",
            ["g", "ml", "szt"],
        )

        package_price = st.number_input(
            "Cena opakowania [zł]",
            min_value=0.01,
            step=0.10,
            format="%.2f",
        )

        submitted = st.form_submit_button(
            "Dodaj składnik"
        )

    if submitted:
        clean_name = name.strip()

        if not clean_name:
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
                    clean_name,
                )

                already_exists = cursor.fetchone()[0] > 0

                if already_exists:
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
                        VALUES (?, ?, ?, ?);
                        """,
                        clean_name,
                        package_quantity,
                        unit,
                        package_price,
                    )

                    connection.commit()

                    st.success("Składnik został dodany.")
                    st.rerun()


# =========================================================
# POBIERANIE SKŁADNIKÓW
# =========================================================

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

    ingredients = [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


# =========================================================
# EDYCJA SKŁADNIKA
# =========================================================

with st.expander("Edytuj składnik", expanded=False):
    if not ingredients:
        st.info("Nie ma jeszcze żadnych składników.")

    else:
        ingredient_by_id = {
            ingredient["ingredient_id"]: ingredient
            for ingredient in ingredients
        }

        selected_id = st.selectbox(
            "Wybierz składnik",
            options=list(ingredient_by_id),
            format_func=lambda ingredient_id: (
                ingredient_by_id[ingredient_id]["name"]
            ),
            key="edit_ingredient_selection",
        )

        selected = ingredient_by_id[selected_id]

        available_units = ["g", "ml", "szt"]

        if selected["unit"] not in available_units:
            available_units.append(selected["unit"])

        with st.form("edit_ingredient_form"):
            edited_name = st.text_input(
                "Nazwa",
                value=selected["name"],
            )

            edited_quantity_text = st.text_input(
                "Ilość w opakowaniu",
                value=(
                    ""
                    if selected["package_quantity"] is None
                    else str(selected["package_quantity"])
                ),
            )

            edited_unit = st.selectbox(
                "Jednostka",
                available_units,
                index=available_units.index(
                    selected["unit"]
                ),
            )

            edited_price_text = st.text_input(
                "Cena opakowania [zł]",
                value=(
                    ""
                    if selected["package_price"] is None
                    else str(selected["package_price"])
                ),
            )

            update_submitted = st.form_submit_button(
                "Zapisz zmiany"
            )

        if update_submitted:
            clean_name = edited_name.strip()

            if not clean_name:
                st.error(
                    "Nazwa składnika nie może być pusta."
                )

            else:
                try:
                    edited_quantity = (
                        float(
                            edited_quantity_text.replace(",", ".")
                        )
                        if edited_quantity_text.strip()
                        else None
                    )

                    edited_price = (
                        float(
                            edited_price_text.replace(",", ".")
                        )
                        if edited_price_text.strip()
                        else None
                    )

                    if (
                        edited_quantity is not None
                        and edited_quantity <= 0
                    ):
                        raise ValueError

                    if (
                        edited_price is not None
                        and edited_price <= 0
                    ):
                        raise ValueError

                except ValueError:
                    st.error(
                        "Ilość i cena muszą być "
                        "dodatnimi liczbami."
                    )

                else:
                    with get_connection() as connection:
                        cursor = connection.cursor()

                        cursor.execute(
                            """
                            SELECT COUNT(*)
                            FROM Ingredients
                            WHERE name = ?
                              AND ingredient_id <> ?;
                            """,
                            clean_name,
                            selected_id,
                        )

                        name_taken = (
                            cursor.fetchone()[0] > 0
                        )

                        if name_taken:
                            st.warning(
                                "Inny składnik ma już "
                                "taką nazwę."
                            )

                        else:
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
                                clean_name,
                                edited_quantity,
                                edited_unit,
                                edited_price,
                                selected_id,
                            )

                            connection.commit()

                            st.success(
                                "Zmiany zostały zapisane."
                            )
                            st.rerun()


# =========================================================
# LISTA SKŁADNIKÓW
# =========================================================

with st.expander("Lista składników", expanded=True):
    if not ingredients:
        st.info("Nie ma jeszcze żadnych składników.")

    else:
        st.dataframe(
            ingredients,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ingredient_id": "ID",
                "name": "Nazwa",
                "package_quantity": "Ilość w opakowaniu",
                "unit": "Jednostka",
                "package_price": (
                    st.column_config.NumberColumn(
                        "Cena opakowania",
                        format="%.2f zł",
                    )
                ),
            },
        )