import streamlit as st

from db import get_connection
from pricing import fetch_rows


st.title("Zamówienia")


# =========================================================
# KOMUNIKATY
# =========================================================

status_message = st.session_state.pop(
    "order_status_message",
    None,
)

if status_message:
    st.success(status_message)


# =========================================================
# POBIERANIE ZAMÓWIEŃ
# =========================================================

orders = fetch_rows("""
    SELECT
        order_id,
        due_date,
        customer_name,
        recipe_name_snapshot,
        status,
        ingredients_cost,
        work_cost,
        total_cost,
        total_cost - work_cost AS cost_without_work,
        selling_price,
        deposit_amount,
        selling_price - deposit_amount
            AS remaining_amount,
        fulfillment_method,
        notes
    FROM Orders
    ORDER BY due_date DESC, order_id DESC;
""")


if not orders:
    st.info(
        "Nie ma jeszcze zapisanych zamówień. "
        "Zamówienie możesz zapisać w pełnej wycenie."
    )
    st.stop()


active_orders = [
    order
    for order in orders
    if order["status"] not in (
        "Odebrane",
        "Zrealizowane",
        "Anulowane",
    )
]

completed_orders = [
    order
    for order in orders
    if order["status"] in (
        "Odebrane",
        "Zrealizowane",
    )
]

cancelled_orders = [
    order
    for order in orders
    if order["status"] == "Anulowane"
]


# =========================================================
# FUNKCJA WYŚWIETLANIA TABELI
# =========================================================

def display_orders(order_rows):
    st.dataframe(
        order_rows,
        use_container_width=True,
        hide_index=True,
        column_order=(
            "order_id",
            "due_date",
            "customer_name",
            "recipe_name_snapshot",
            "status",
            "cost_without_work",
            "selling_price",
            "deposit_amount",
            "remaining_amount",
        ),
        column_config={
            "order_id": "Nr",
            "due_date": st.column_config.DatetimeColumn(
                "Termin",
                format="DD.MM.YYYY HH:mm",
            ),
            "customer_name": "Klient",
            "recipe_name_snapshot": "Zamówienie",
            "status": "Status",
            "cost_without_work": st.column_config.NumberColumn(
                "Koszt bez robocizny",
                format="%.2f zł",
            ),
            "selling_price": (
                st.column_config.NumberColumn(
                    "Cena sprzedaży",
                    format="%.2f zł",
                )
            ),
            "deposit_amount": (
                st.column_config.NumberColumn(
                    "Zapłacono",
                    format="%.2f zł",
                )
            ),
            "remaining_amount": (
                st.column_config.NumberColumn(
                    "Pozostało",
                    format="%.2f zł",
                )
            ),
        },
    )


# =========================================================
# LISTY ZAMÓWIEŃ
# =========================================================

with st.expander(
    f"Aktywne zamówienia ({len(active_orders)})",
    expanded=True,
):
    if active_orders:
        display_orders(active_orders)
    else:
        st.info("Brak aktywnych zamówień.")


with st.expander(
    f"Zrealizowane zamówienia ({len(completed_orders)})",
    expanded=True,
):
    if completed_orders:
        display_orders(completed_orders)
    else:
        st.info("Brak zrealizowanych zamówień.")


with st.expander(
    f"Anulowane zamówienia ({len(cancelled_orders)})",
    expanded=False,
):
    if cancelled_orders:
        display_orders(cancelled_orders)
    else:
        st.info("Brak anulowanych zamówień.")


# =========================================================
# SZCZEGÓŁY ZAMÓWIENIA
# =========================================================

st.header("Szczegóły zamówienia")

order_by_id = {
    order["order_id"]: order
    for order in orders
}

selected_order_id = st.selectbox(
    "Wybierz zamówienie",
    options=list(order_by_id),
    format_func=lambda order_id: (
        f"Nr {order_id} — "
        f"{order_by_id[order_id]['customer_name']} — "
        f"{order_by_id[order_id]['status']}"
    ),
)

selected_order = order_by_id[selected_order_id]


# =========================================================
# PODSUMOWANIE FINANSOWE
# =========================================================

selling_price = float(
    selected_order["selling_price"]
)

cost_without_work = float(
    selected_order["cost_without_work"]
)

work_cost = float(
    selected_order["work_cost"]
)

deposit_amount = float(
    selected_order["deposit_amount"]
)

# Kwota, która zostaje dla Ciebie po pokryciu wydatków
total_earnings = (
    selling_price - cost_without_work
)

# Część ponad zaplanowane wynagrodzenie za pracę
additional_profit = (
    total_earnings - work_cost
)
summary_col1, summary_col2 = st.columns(2)
summary_col3, summary_col4 = st.columns(2)

summary_col1.metric(
    "Koszt bez robocizny",
    f"{cost_without_work:.2f} zł",
)

summary_col2.metric(
    "Cena sprzedaży",
    f"{selling_price:.2f} zł",
)

summary_col3.metric(
    "Zapłacono",
    f"{deposit_amount:.2f} zł",
)

summary_col4.metric(
    "Pozostało",
    f"{selling_price - deposit_amount:.2f} zł",
)

st.metric(
    "Wynagrodzenie i dodatkowy zysk",
    f"{total_earnings:.2f} zł",
)


# =========================================================
# POZYCJE ZAMÓWIENIA
# =========================================================

with st.expander(
    "Pozycje zamówienia",
    expanded=True,
):
    order_items = fetch_rows(
        """
        SELECT
            position_number,
            recipe_name_snapshot,
            target_diameter_cm,
            target_height_cm,
            multiplier,
            ingredients_cost
        FROM OrderRecipeItems
        WHERE order_id = ?
        ORDER BY position_number;
        """,
        (selected_order_id,),
    )

    if order_items:
        st.dataframe(
            order_items,
            use_container_width=True,
            hide_index=True,
            column_config={
                "position_number": "Lp.",
                "recipe_name_snapshot": "Przepis",
                "target_diameter_cm": (
                    st.column_config.NumberColumn(
                        "Średnica",
                        format="%.1f cm",
                    )
                ),
                "target_height_cm": (
                    st.column_config.NumberColumn(
                        "Wysokość",
                        format="%.1f cm",
                    )
                ),
                "multiplier": (
                    st.column_config.NumberColumn(
                        "Mnożnik",
                        format="× %.3f",
                    )
                ),
                "ingredients_cost": (
                    st.column_config.NumberColumn(
                        "Koszt składników",
                        format="%.2f zł",
                    )
                ),
            },
        )
    else:
        st.info(
            "To starsze zamówienie nie ma zapisanych "
            "oddzielnych pozycji."
        )


# =========================================================
# SNAPSHOT SKŁADNIKÓW
# =========================================================

with st.expander(
    "Składniki zamówienia",
    expanded=False,
):
    order_ingredients = fetch_rows(
        """
        SELECT
            COALESCE(
                ori.recipe_name_snapshot,
                o.recipe_name_snapshot
            ) AS recipe,
            oi.ingredient_name_snapshot
                AS ingredient,
            oi.scaled_quantity,
            oi.unit,
            oi.package_quantity_snapshot,
            oi.package_price_snapshot,
            oi.ingredient_cost
        FROM OrderIngredients AS oi

        JOIN Orders AS o
            ON o.order_id = oi.order_id

        LEFT JOIN OrderRecipeItems AS ori
            ON ori.order_recipe_item_id
                = oi.order_recipe_item_id

        WHERE oi.order_id = ?

        ORDER BY
            ori.position_number,
            oi.ingredient_name_snapshot;
        """,
        (selected_order_id,),
    )

    if order_ingredients:
        st.dataframe(
            order_ingredients,
            use_container_width=True,
            hide_index=True,
            column_config={
                "recipe": "Pozycja",
                "ingredient": "Składnik",
                "scaled_quantity": "Ilość",
                "unit": "Jednostka",
                "package_quantity_snapshot": (
                    "Ilość w opakowaniu"
                ),
                "package_price_snapshot": (
                    st.column_config.NumberColumn(
                        "Cena opakowania",
                        format="%.2f zł",
                    )
                ),
                "ingredient_cost": (
                    st.column_config.NumberColumn(
                        "Koszt",
                        format="%.2f zł",
                    )
                ),
            },
        )
    else:
        st.info(
            "Zamówienie nie ma zapisanych składników."
        )


# =========================================================
# UWAGI
# =========================================================

if selected_order["notes"]:
    with st.expander("Uwagi", expanded=False):
        st.write(selected_order["notes"])


# =========================================================
# ZMIANA STATUSU
# =========================================================

with st.expander("Zmień status", expanded=False):
    available_statuses = [
        "Nowe",
        "W trakcie",
        "Gotowe",
        "Odebrane",
        "Anulowane",
    ]

    current_status = selected_order["status"]

    if current_status not in available_statuses:
        available_statuses.append(current_status)

    new_status = st.selectbox(
        "Status",
        options=available_statuses,
        index=available_statuses.index(
            current_status
        ),
    )

    if st.button(
        "Zapisz status",
        type="primary",
    ):
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE Orders
                SET
                    status = ?,
                    updated_at = SYSDATETIME()
                WHERE order_id = ?;
                """,
                new_status,
                selected_order_id,
            )

            connection.commit()

        st.session_state.order_status_message = (
            f"Status zamówienia nr {selected_order_id} "
            f"zmieniono na „{new_status}”."
        )

        st.rerun()