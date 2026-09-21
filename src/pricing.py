from db import get_connection


def fetch_rows(query, parameters=()):
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
    scale_factor_override=None,
):
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

    base_diameter = float(
        recipe["base_diameter_cm"]
    )
    base_height = float(
        recipe["base_height_cm"]
    )

    target_diameter = float(target_diameter)
    target_height = float(target_height)
    correction_percent = float(correction_percent)

    if target_diameter <= 0:
        raise ValueError(
            "Średnica musi być większa od zera."
        )

    if target_height <= 0:
        raise ValueError(
            "Wysokość musi być większa od zera."
        )

    if correction_percent <= -100:
        raise ValueError(
            "Korekta nie może wynosić -100% lub mniej."
        )

    automatic_scale_factor = (
        (target_diameter / base_diameter) ** 2
        * (target_height / base_height)
        * (1 + correction_percent / 100)
    )
    
    if scale_factor_override is None:
        scale_factor = automatic_scale_factor
    else:
        scale_factor = float(scale_factor_override)
    
        if scale_factor <= 0:
            raise ValueError(
                "Mnożnik musi być większy od zera."
            )

    ingredients = fetch_rows(
        """
        WITH RecipeTree AS (
            SELECT
                CAST(? AS INT) AS recipe_id,

                CAST(
                    1.0 AS DECIMAL(18,6)
                ) AS recipe_factor,

                CAST(
                    N'/'
                    + CAST(? AS NVARCHAR(20))
                    + N'/'
                    AS NVARCHAR(MAX)
                ) AS recipe_path

            UNION ALL

            SELECT
                rc.child_recipe_id,

                CAST(
                    rt.recipe_factor
                    * rc.quantity_factor
                    AS DECIMAL(18,6)
                ) AS recipe_factor,

                CAST(
                    rt.recipe_path
                    + CAST(
                        rc.child_recipe_id
                        AS NVARCHAR(20)
                    )
                    + N'/'
                    AS NVARCHAR(MAX)
                ) AS recipe_path

            FROM RecipeTree AS rt

            JOIN RecipeComponents AS rc
                ON rc.parent_recipe_id
                    = rt.recipe_id

            WHERE rt.recipe_path NOT LIKE
                N'%/'
                + CAST(
                    rc.child_recipe_id
                    AS NVARCHAR(20)
                )
                + N'/%'
        ),

        BaseIngredients AS (
            SELECT
                i.ingredient_id,
                i.name AS ingredient,
                i.unit,
                i.package_quantity,
                i.package_price,

                SUM(
                    CAST(
                        ri.quantity
                        AS DECIMAL(18,6)
                    )
                    * rt.recipe_factor
                ) AS base_quantity

            FROM RecipeTree AS rt

            JOIN RecipeIngredients AS ri
                ON ri.recipe_id = rt.recipe_id

            JOIN Ingredients AS i
                ON i.ingredient_id
                    = ri.ingredient_id

            GROUP BY
                i.ingredient_id,
                i.name,
                i.unit,
                i.package_quantity,
                i.package_price
        ),

        ScaledIngredients AS (
            SELECT
                ingredient_id,
                ingredient,
                unit,
                package_quantity,
                package_price,
                base_quantity,

                CASE
                    WHEN LOWER(
                        LTRIM(RTRIM(unit))
                    ) IN (N'szt', N'szt.')
                    THEN CEILING(
                        base_quantity * ?
                    )
                    ELSE ROUND(
                        base_quantity * ?,
                        0
                    )
                END AS scaled_quantity

            FROM BaseIngredients
        )

        SELECT
            ingredient_id,
            ingredient,
            unit,
            package_quantity,
            package_price,
            base_quantity,
            scaled_quantity,

            CASE
                WHEN package_quantity IS NULL
                  OR package_price IS NULL
                THEN NULL

                ELSE ROUND(
                    scaled_quantity
                    / NULLIF(package_quantity, 0)
                    * package_price,
                    2
                )
            END AS ingredient_cost

        FROM ScaledIngredients

        ORDER BY ingredient

        OPTION (MAXRECURSION 100);
        """,
        (
            recipe_id,
            recipe_id,
            scale_factor,
            scale_factor,
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