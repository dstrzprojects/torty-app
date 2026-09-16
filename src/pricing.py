from db import get_connection


def fetch_rows(query, parameters=()):
    """Wykonuje SELECT i zwraca listę słowników."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, parameters)

        columns = [
            column[0]
            for column in cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def fetch_one(query, parameters=()):
    """Wykonuje SELECT i zwraca jeden wiersz jako słownik."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, parameters)

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [
            column[0]
            for column in cursor.description
        ]

        return dict(zip(columns, row))


def get_recipes():
    """Pobiera przepisy dostępne do wyceny."""
    return fetch_rows("""
        SELECT
            recipe_id,
            name,
            base_diameter_cm,
            base_height_cm
        FROM Recipes
        ORDER BY name;
    """)


def calculate_scaled_ingredients(
    recipe_id,
    target_diameter,
    target_height,
    correction_percent=0,
):
    """
    Skaluje ilości składników i wylicza ich koszty.

    Zwraca słownik zawierający:
    - recipe,
    - scale_factor,
    - ingredients,
    - ingredients_cost,
    - missing_price_ingredients.
    """

    recipe = fetch_one(
        """
        SELECT
            recipe_id,
            name,
            base_diameter_cm,
            base_height_cm
        FROM Recipes
        WHERE recipe_id = ?;
        """,
        (recipe_id,),
    )

    if recipe is None:
        raise ValueError("Wybrany przepis nie istnieje.")

    base_diameter = float(recipe["base_diameter_cm"])
    base_height = float(recipe["base_height_cm"])

    target_diameter = float(target_diameter)
    target_height = float(target_height)
    correction_percent = float(correction_percent)

    if target_diameter <= 0:
        raise ValueError(
            "Średnica docelowa musi być większa od zera."
        )

    if target_height <= 0:
        raise ValueError(
            "Wysokość docelowa musi być większa od zera."
        )

    if correction_percent <= -100:
        raise ValueError(
            "Korekta nie może wynosić -100% lub mniej."
        )

    scale_factor = (
        (target_diameter / base_diameter) ** 2
        * (target_height / base_height)
        * (1 + correction_percent / 100)
    )

    ingredients = fetch_rows(
        """
        SELECT
            i.ingredient_id,
            i.name AS ingredient,
            i.unit,
            i.package_quantity,
            i.package_price,
            ri.quantity AS base_quantity,
            CASE
                WHEN LOWER(LTRIM(RTRIM(i.unit))) IN (N'szt', N'szt.')
                THEN CEILING(ri.quantity * ?)
                ELSE ROUND(ri.quantity * ?, 0)
            END AS scaled_quantity,

            CASE
                WHEN i.package_quantity IS NULL
                  OR i.package_price IS NULL
                THEN NULL

                ELSE ROUND(
                    (
                        CASE
                            WHEN LOWER(LTRIM(RTRIM(i.unit))) IN (N'szt', N'szt.')
                            THEN CEILING(ri.quantity * ?)
                            ELSE ROUND(ri.quantity * ?, 0)
                        END
                    )
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
        (
            scale_factor,
            scale_factor,
            scale_factor,
            scale_factor,
            recipe_id,
        ),
    )

    known_costs = [
        float(row["ingredient_cost"])
        for row in ingredients
        if row["ingredient_cost"] is not None
    ]

    missing_price_ingredients = [
        row["ingredient"]
        for row in ingredients
        if row["ingredient_cost"] is None
    ]

    return {
        "recipe": recipe,
        "scale_factor": scale_factor,
        "ingredients": ingredients,
        "ingredients_cost": sum(known_costs),
        "missing_price_ingredients": (
            missing_price_ingredients
        ),
    }