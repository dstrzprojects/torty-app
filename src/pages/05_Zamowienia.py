from datetime import datetime, timedelta

import streamlit as st

from db import get_connection
from pricing import (
    calculate_scaled_ingredients,
    fetch_rows,
    get_recipes,
)

st.title("Zamówienia")

recipes = get_recipes()

if not recipes:
    st.info("Najpierw utwórz przepis.")
    st.stop()

recipe_by_id = {
    recipe["recipe_id"]: recipe
    for recipe in recipes
}


# =========================================================
# NOWE ZAMÓWIENIE
# =========================================================

with st.expander("Nowe zamówienie", expanded=True):
    st.subheader("Klient i termin")

    customer_col1, customer_col2 = st.columns(2)

    with customer_col1:
        customer_name = st.text_input(
            "Imię i nazwisko klienta"
        )

        customer_phone = st.text_input(
            "Telefon — opcjonalnie"
        )

        due_date = st.date_input(
            "Data realizacji",
            value=datetime.now().date()
            + timedelta(days=7),
        )

        due_time = st.time_input(
            "Godzina realizacji",
            value=datetime.strptime(
                "12:00",
                "%H:%M",
            ).time(),
        )

    with customer_col2:
        fulfillment_method = st.selectbox(
            "Sposób przekazania",
            ["Odbiór osobisty", "Dostawa"],
        )

        delivery_address = st.text_area(
            "Adres dostawy",
            disabled=(
                fulfillment_method
                != "Dostawa"
            ),
        )

        notes = st.text_area(
            "Uwagi do zamówienia",
            placeholder=(
                "Dekoracje, napis, alergie, "
                "preferencje klienta..."
            ),
        )

    st.subheader("Tort")

    selected_recipe_id = st.selectbox(
        "Przepis",
        options=list(recipe_by_id),
        format_func=lambda recipe_id: (
            recipe_by_id[recipe_id]["name"]
        ),
        key="order_recipe",
    )

    selected_recipe = recipe_by_id[
        selected_recipe_id
    ]

    base_diameter = float(
        selected_recipe["base_diameter_cm"]
    )

    base_height = float(
        selected_recipe["base_height_cm"]
    )

    dimensions_col1, dimensions_col2 = st.columns(2)

    with dimensions_col1:
        target_diameter = st.number_input(
            "Średnica [cm]",
            min_value=1.0,
            value=base_diameter,
            step=1.0,
            key=f"order_diameter_{selected_recipe_id}",
        )

    with dimensions_col2:
        target_height = st.number_input(
            "Wysokość [cm]",
            min_value=1.0,
            value=base_height,
            step=1.0,
            key=f"order_height_{selected_recipe_id}",
        )

    correction_percent = st.number_input(
        "Korekta ilości składników [%]",
        min_value=-50.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
        key=f"order_correction_{selected_recipe_id}",
    )

    pricing_result = calculate_scaled_ingredients(
        recipe_id=selected_recipe_id,
        target_diameter=target_diameter,
        target_height=target_height,
        correction_percent=correction_percent,
    )

    ingredient_rows = pricing_result["ingredients"]
    ingredients_cost = pricing_result[
        "ingredients_cost"
    ]
    missing_prices = pricing_result[
        "missing_price_ingredients"
    ]

    if missing_prices:
        st.error(
            "Nie można poprawnie wycenić zamówienia. "
            "Brakuje ceny lub wielkości opakowania dla: "
            + ", ".join(missing_prices)
        )

    st.metric(
        "Koszt składników",
        f"{ingredients_cost:.2f} zł",
    )

    st.subheader("Pozostałe koszty")

    costs_col1, costs_col2 = st.columns(2)

    with costs_col1:
        work_hours = st.number_input(
            "Czas pracy [godz.]",
            min_value=0.0,
            value=4.0,
            step=0.5,
            key="order_work_hours",
        )

        hourly_rate = st.number_input(
            "Stawka godzinowa [zł]",
            min_value=0.0,
            value=30.0,
            step=5.0,
            key="order_hourly_rate",
        )

        utilities_cost = st.number_input(
            "Media [zł]",
            min_value=0.0,
            value=10.0,
            step=1.0,
            key="order_utilities",
        )

    with costs_col2:
        depreciation_cost = st.number_input(
            "Amortyzacja [zł]",
            min_value=0.0,
            value=5.0,
            step=1.0,
            key="order_depreciation",
        )

        decorations_cost = st.number_input(
            "Dekoracje i dodatki [zł]",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="order_decorations",
        )

        packaging_cost = st.number_input(
            "Opakowanie [zł]",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="order_packaging",
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

    st.subheader("Cena i zaliczka")

    markup_percent = st.number_input(
        "Sugerowany narzut [%]",
        min_value=0.0,
        value=0.0,
        step=5.0,
        key="order_markup",
    )

    suggested_price = total_cost * (
        1 + markup_percent / 100
    )

    st.metric(
        "Cena sugerowana",
        f"{suggested_price:.2f} zł",
    )

    selling_price = st.number_input(
        "Cena uzgodniona z klientem [zł]",
        min_value=0.0,
        value=float(round(suggested_price, 2)),
        step=10.0,
        format="%.2f",
        key="order_selling_price",
    )

    deposit_amount = st.number_input(
        "Wpłacona zaliczka [zł]",
        min_value=0.0,
        value=0.0,
        step=10.0,
        format="%.2f",
        key="order_deposit",
    )

    remaining_amount = (
        selling_price - deposit_amount
    )

    price_col1, price_col2, price_col3 = st.columns(3)

    price_col1.metric(
        "Koszt wykonania",
        f"{total_cost:.2f} zł",
    )

    price_col2.metric(
        "Cena sprzedaży",
        f"{selling_price:.2f} zł",
    )

    price_col3.metric(
        "Pozostało do zapłaty",
        f"{remaining_amount:.2f} zł",
    )

    save_order = st.button(
        "Zapisz zamówienie",
        type="primary",
        disabled=bool(missing_prices),
    )

    if save_order:
        clean_customer_name = customer_name.strip()
        clean_phone = customer_phone.strip()
        clean_address = delivery_address.strip()
        clean_notes = notes.strip()

        if not clean_customer_name:
            st.error("Podaj imię i nazwisko klienta.")

        elif (
            fulfillment_method == "Dostawa"
            and not clean_address
        ):
            st.error("Podaj adres dostawy.")

        elif deposit_amount > selling_price:
            st.error(
                "Zaliczka nie może być większa "
                "od ceny sprzedaży."
            )

        elif not ingredient_rows:
            st.error(
                "Wybrany przepis nie ma składników."
            )

        else:
            due_datetime = datetime.combine(
                due_date,
                due_time,
            )

            connection = get_connection()

            try:
                cursor = connection.cursor()

                cursor.execute(
                    """
                    INSERT INTO Orders (
                        recipe_id,
                        recipe_name_snapshot,
                        customer_name,
                        customer_phone,
                        target_diameter_cm,
                        target_height_cm,
                        correction_percent,
                        due_date,
                        status,
                        ingredients_cost,
                        work_hours,
                        hourly_rate,
                        work_cost,
                        utilities_cost,
                        depreciation_cost,
                        decorations_cost,
                        packaging_cost,
                        markup_percent,
                        total_cost,
                        selling_price,
                        deposit_amount,
                        fulfillment_method,
                        delivery_address,
                        notes
                    )
                    OUTPUT INSERTED.order_id
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        N'Nowe',
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?
                    );
                    """,
                    selected_recipe_id,
                    selected_recipe["name"],
                    clean_customer_name,
                    clean_phone or None,
                    target_diameter,
                    target_height,
                    correction_percent,
                    due_datetime,
                    ingredients_cost,
                    work_hours,
                    hourly_rate,
                    work_cost,
                    utilities_cost,
                    depreciation_cost,
                    decorations_cost,
                    packaging_cost,
                    markup_percent,
                    total_cost,
                    selling_price,
                    deposit_amount,
                    fulfillment_method,
                    (
                        clean_address
                        if fulfillment_method == "Dostawa"
                        else None
                    ),
                    clean_notes or None,
                )

                order_id = cursor.fetchone()[0]

                for ingredient in ingredient_rows:
                    cursor.execute(
                        """
                        INSERT INTO OrderIngredients (
                            order_id,
                            ingredient_id,
                            ingredient_name_snapshot,
                            scaled_quantity,
                            unit,
                            package_quantity_snapshot,
                            package_price_snapshot,
                            ingredient_cost
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        order_id,
                        ingredient["ingredient_id"],
                        ingredient["ingredient"],
                        ingredient["scaled_quantity"],
                        ingredient["unit"],
                        ingredient["package_quantity"],
                        ingredient["package_price"],
                        ingredient["ingredient_cost"],
                    )

                connection.commit()

                st.success(
                    f"Zamówienie nr {order_id} "
                    "zostało zapisane."
                )

            except Exception:
                connection.rollback()
                raise

            finally:
                connection.close()


# =========================================================
# AKTYWNE ZAMÓWIENIA
# =========================================================

with st.expander(
    "Aktywne zamówienia",
    expanded=True,
):
    active_orders = fetch_rows("""
        SELECT
            order_id,
            due_date,
            customer_name,
            recipe_name_snapshot,
            target_diameter_cm,
            target_height_cm,
            selling_price,
            deposit_amount,
            selling_price - deposit_amount
                AS remaining_amount,
            fulfillment_method,
            status
        FROM Orders
        WHERE status NOT IN (
            N'Odebrane',
            N'Anulowane'
        )
        ORDER BY due_date, order_id;
    """)

    if not active_orders:
        st.info("Brak aktywnych zamówień.")

    else:
        st.dataframe(
            active_orders,
            use_container_width=True,
            hide_index=True,
            column_config={
                "order_id": "Nr",
                "due_date": "Termin",
                "customer_name": "Klient",
                "recipe_name_snapshot": "Tort",
                "target_diameter_cm": "Średnica",
                "target_height_cm": "Wysokość",
                "selling_price": (
                    st.column_config.NumberColumn(
                        "Cena",
                        format="%.2f zł",
                    )
                ),
                "deposit_amount": (
                    st.column_config.NumberColumn(
                        "Zaliczka",
                        format="%.2f zł",
                    )
                ),
                "remaining_amount": (
                    st.column_config.NumberColumn(
                        "Pozostało",
                        format="%.2f zł",
                    )
                ),
                "fulfillment_method": "Przekazanie",
                "status": "Status",
            },
        )