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
    unit = st.selectbox("Jednostka", ["g", "ml", "szt."])
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

st.header("Lista składników")

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