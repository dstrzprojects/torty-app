USE TortyDB;
GO

SET XACT_ABORT ON;
--https://ciastkozercy.pl/tort-oreo/--
BEGIN TRY
    BEGIN TRANSACTION;

    -- Usunięcie dotychczasowych danych testowych.
    -- Najpierw tabele zależne, potem nadrzędne.

    IF OBJECT_ID('dbo.CakeCosts', 'U') IS NOT NULL
        DELETE FROM dbo.CakeCosts;

    DELETE FROM dbo.RecipeIngredients;
    DELETE FROM dbo.Recipes;
    DELETE FROM dbo.Ingredients;


    -- Produkty i ceny opakowań

    INSERT INTO dbo.Ingredients (
        name,
        package_quantity,
        unit,
        package_price
    )
    VALUES
        (N'Jajka M',                         10,   N'szt', 8.49),
        (N'Mąka pszenna typ 650',          1000,  N'g',   2.19),
        (N'Kakao ciemne',                    80,   N'g',   9.99),
        (N'Skrobia ziemniaczana',          1000,  N'g',   5.85),
        (N'Cukier biały',                  1000,  N'g',   3.29),
        (N'Mascarpone Delikate',            250,  N'g',   6.99),
        (N'Śmietanka kremówka 36%',         500,  N'ml', 10.99),
        (N'Cukier puder',                   500,  N'g',   2.49),
        (N'Dżem z czarnej porzeczki',       280,  N'g',   7.99),
        (N'Ciastka Oreo Original',            4,  N'szt', 1.99),
        (N'Czekolada gorzka',               100,  N'g',   5.49),
        (N'Olej kokosowy',                  500,  N'g',  14.99);


    -- Przepis bazowy

    INSERT INTO dbo.Recipes (
        name,
        description,
        base_diameter_cm,
        base_height_cm
    )
    VALUES (
        N'Tort Oreo',
        N'Tort Oreo na podstawie przepisu Ciastkożercy. '
        + N'Dwa blaty biszkoptowe, krem mascarpone, Oreo, '
        + N'dżem porzeczkowy i polewa czekoladowa.',
        24,
        10
    );

    DECLARE @RecipeId INT = SCOPE_IDENTITY();


    -- Ilości wykorzystane w całym torcie

    INSERT INTO dbo.RecipeIngredients (
        recipe_id,
        ingredient_id,
        quantity
    )
    SELECT
        @RecipeId,
        i.ingredient_id,
        recipe_data.quantity
    FROM (
        VALUES
            (N'Jajka M',                       6.0),
            (N'Mąka pszenna typ 650',        130.0),
            (N'Kakao ciemne',                 48.0),
            (N'Skrobia ziemniaczana',         60.0),
            (N'Cukier biały',                225.0),
            (N'Mascarpone Delikate',         500.0),
            (N'Śmietanka kremówka 36%',      800.0),
            (N'Cukier puder',                 10.0),
            (N'Dżem z czarnej porzeczki',    200.0),
            (N'Ciastka Oreo Original',        24.0),
            (N'Czekolada gorzka',             50.0),
            (N'Olej kokosowy',                 5.0)
    ) AS recipe_data(ingredient_name, quantity)
    JOIN dbo.Ingredients AS i
        ON i.name = recipe_data.ingredient_name;

    COMMIT TRANSACTION;

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO


-- Kontrola wstawionych danych i kosztów

SELECT
    r.name AS recipe,
    r.base_diameter_cm,
    r.base_height_cm,
    i.name AS ingredient,
    ri.quantity,
    i.unit,
    i.package_quantity,
    i.package_price,
    ROUND(
        ri.quantity / i.package_quantity * i.package_price,
        2
    ) AS ingredient_cost
FROM dbo.RecipeIngredients AS ri
JOIN dbo.Recipes AS r
    ON r.recipe_id = ri.recipe_id
JOIN dbo.Ingredients AS i
    ON i.ingredient_id = ri.ingredient_id
ORDER BY i.name;
GO