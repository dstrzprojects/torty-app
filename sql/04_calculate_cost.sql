WITH IngredientCosts AS (
    SELECT
        ri.recipe_id,
        SUM(
            ri.quantity / i.package_quantity
            * i.package_price
        ) AS ingredients_cost
    FROM RecipeIngredients ri
    JOIN Ingredients i
        ON i.ingredient_id = ri.ingredient_id
    GROUP BY ri.recipe_id
)
SELECT
    r.name AS recipe_name,
    ROUND(ic.ingredients_cost, 2) AS ingredients_cost,
    cc.work_hours * cc.hourly_rate AS labour_cost,
    cc.utilities_cost,
    cc.equipment_depreciation,
    cc.additional_cost,

    ROUND(
        ic.ingredients_cost
        + cc.work_hours * cc.hourly_rate
        + cc.utilities_cost
        + cc.equipment_depreciation
        + cc.additional_cost,
        2
    ) AS total_cost

FROM Recipes r
JOIN IngredientCosts ic
    ON ic.recipe_id = r.recipe_id
JOIN CakeCosts cc
    ON cc.recipe_id = r.recipe_id;