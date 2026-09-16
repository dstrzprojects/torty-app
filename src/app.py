import streamlit as st

from db import get_connection

st.set_page_config(
    page_title="Wycena tortów",
    page_icon="🎂",
)

st.title("Wycena tortów")

st.header("Dodaj składnik")

with st.form("ingredient_form", clear_on_submit=True):
    name = st.text_input("Nazwa składnika")
    package_quantity = st.number_input(
        "Ilość w opakowaniu",
        min_value=0.01,
        step=1.0,
    )
    unit = st.selectbox("Jednostka", ["g", "ml", "szt"])
    package_price = st.number_input(
        "Cena opakowania [zł]",
        min_value=0.01,
        step=0.10,
        format="%.2f",
    )

    submitted = st.form_submit_button("Dodaj składnik")

if submitted:
    clean_name = name.strip()

    if not clean_name:
        st.error("Podaj nazwę składnika.")
    else:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM Ingredients WHERE name = ?;",
                clean_name,
            )
            already_exists = cursor.fetchone()[0] > 0

            if already_exists:
                st.warning("Składnik o takiej nazwie już istnieje.")
            else:
                cursor.execute(
                    """
                    INSERT INTO Ingredients
                        (name, package_quantity, unit, package_price)
                    VALUES (?, ?, ?, ?);
                    """,
                    clean_name,
                    package_quantity,
                    unit,
                    package_price,
                )
                connection.commit()
                st.success("Składnik został dodany.")





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

    columns = [column[0] for column in cursor.description]
    ingredients = [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

st.header("Edytuj składnik")

if ingredients:
    ingredient_by_id = {
        ingredient["ingredient_id"]: ingredient
        for ingredient in ingredients
    }

    selected_id = st.selectbox(
        "Wybierz składnik",
        options=list(ingredient_by_id),
        format_func=lambda ingredient_id: ingredient_by_id[ingredient_id]["name"],
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
        edited_quantity = st.number_input(
            "Ilość w opakowaniu",
            min_value=0.01,
            value=float(selected["package_quantity"]),
            step=1.0,
        )
        edited_unit = st.selectbox(
            "Jednostka",
            available_units,
            index=available_units.index(selected["unit"]),
        )
        edited_price = st.number_input(
            "Cena opakowania [zł]",
            min_value=0.01,
            value=float(selected["package_price"]),
            step=0.10,
            format="%.2f",
        )

        update_submitted = st.form_submit_button("Zapisz zmiany")

    if update_submitted:
        clean_name = edited_name.strip()

        if not clean_name:
            st.error("Nazwa składnika nie może być pusta.")
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

                name_taken = cursor.fetchone()[0] > 0

                if name_taken:
                    st.warning("Inny składnik ma już taką nazwę.")
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

                    st.success("Zmiany zostały zapisane.")
                    st.rerun()

st.header("Lista składników")

st.dataframe(
    ingredients,
    use_container_width=True,
    hide_index=True,
    column_config={
        "ingredient_id": "ID",
        "name": "Nazwa",
        "package_quantity": "Ilość",
        "unit": "Jednostka",
        "package_price": st.column_config.NumberColumn(
            "Cena opakowania",
            format="%.2f zł",
        ),
    },
)