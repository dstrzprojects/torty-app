USE TortyDB;
GO

-- 1. Dodanie składników
INSERT INTO Ingredients
    (name, package_quantity, unit, package_price)
VALUES
    (N'Mąka',       1000, N'g',   4.50),
    (N'Cukier',     1000, N'g',   5.00),
    (N'Jajka',        10, N'szt', 12.00),
    (N'Śmietanka',   500, N'ml',  8.50),
    (N'Czekolada',   200, N'g',   9.00);

-- 2. Dodanie przepisu
INSERT INTO Recipes (name, description)
VALUES (
    N'Tort czekoladowy',
    N'Przykładowy tort testowy'
);

-- 3. Połączenie składników z przepisem
DECLARE @recipe_id INT;

SELECT @recipe_id = recipe_id
FROM Recipes
WHERE name = N'Tort czekoladowy';

INSERT INTO RecipeIngredients
    (recipe_id, ingredient_id, quantity)
SELECT @recipe_id, ingredient_id,
    CASE name
        WHEN N'Mąka' THEN 400
        WHEN N'Cukier' THEN 150
        WHEN N'Jajka' THEN 6
        WHEN N'Śmietanka' THEN 600
        WHEN N'Czekolada' THEN 300
    END
FROM Ingredients
WHERE name IN (
    N'Mąka',
    N'Cukier',
    N'Jajka',
    N'Śmietanka',
    N'Czekolada'
);

-- 4. Dodanie kosztów dodatkowych
INSERT INTO CakeCosts (
    recipe_id,
    work_hours,
    hourly_rate,
    utilities_cost,
    equipment_depreciation,
    additional_cost
)
VALUES (
    @recipe_id,
    3,      -- godziny pracy
    30,     -- zł za godzinę
    8,      -- media
    5,      -- amortyzacja
    4       -- pozostałe koszty
);
GO