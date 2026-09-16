USE TortyDB;
GO

-- Dodanie średnicy bazowej, jeśli kolumna jeszcze nie istnieje
IF COL_LENGTH('dbo.Recipes', 'base_diameter_cm') IS NULL
BEGIN
    ALTER TABLE dbo.Recipes
    ADD base_diameter_cm DECIMAL(5,2)
        NOT NULL
        CONSTRAINT DF_Recipes_BaseDiameter DEFAULT 20;
END;
GO

-- Dodanie wysokości bazowej, jeśli kolumna jeszcze nie istnieje
IF COL_LENGTH('dbo.Recipes', 'base_height_cm') IS NULL
BEGIN
    ALTER TABLE dbo.Recipes
    ADD base_height_cm DECIMAL(5,2)
        NOT NULL
        CONSTRAINT DF_Recipes_BaseHeight DEFAULT 10;
END;
GO

-- Zabezpieczenie przed zerową lub ujemną średnicą
IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_Recipes_BaseDiameter_Positive'
)
BEGIN
    ALTER TABLE dbo.Recipes
    ADD CONSTRAINT CK_Recipes_BaseDiameter_Positive
        CHECK (base_diameter_cm > 0);
END;
GO

-- Zabezpieczenie przed zerową lub ujemną wysokością
IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_Recipes_BaseHeight_Positive'
)
BEGIN
    ALTER TABLE dbo.Recipes
    ADD CONSTRAINT CK_Recipes_BaseHeight_Positive
        CHECK (base_height_cm > 0);
END;
GO

SELECT
    recipe_id,
    name,
    base_diameter_cm,
    base_height_cm
FROM dbo.Recipes;
GO