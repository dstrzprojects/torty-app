USE TortyDB;
GO


-- =========================================================
-- POZYCJE ZAMÓWIENIA
-- Jedno zamówienie może zawierać wiele przepisów,
-- również kilka egzemplarzy tego samego przepisu.
-- =========================================================

IF OBJECT_ID(
    'dbo.OrderRecipeItems',
    'U'
) IS NULL
BEGIN
    CREATE TABLE dbo.OrderRecipeItems (
        order_recipe_item_id INT
            IDENTITY(1,1)
            NOT NULL,

        order_id INT NOT NULL,

        recipe_id INT NULL,

        recipe_name_snapshot NVARCHAR(200)
            NOT NULL,

        target_diameter_cm DECIMAL(10,2)
            NOT NULL,

        target_height_cm DECIMAL(10,2)
            NOT NULL,

        multiplier DECIMAL(18,6)
            NOT NULL,

        ingredients_cost DECIMAL(12,2)
            NOT NULL,

        position_number INT
            NOT NULL,

        created_at DATETIME2
            NOT NULL
            CONSTRAINT DF_OrderRecipeItems_CreatedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT PK_OrderRecipeItems
            PRIMARY KEY (order_recipe_item_id),

        CONSTRAINT FK_OrderRecipeItems_Orders
            FOREIGN KEY (order_id)
            REFERENCES dbo.Orders(order_id)
            ON DELETE CASCADE,

        CONSTRAINT FK_OrderRecipeItems_Recipes
            FOREIGN KEY (recipe_id)
            REFERENCES dbo.Recipes(recipe_id)
            ON DELETE SET NULL,

        CONSTRAINT CK_OrderRecipeItems_Multiplier
            CHECK (multiplier > 0),

        CONSTRAINT CK_OrderRecipeItems_Dimensions
            CHECK (
                target_diameter_cm > 0
                AND target_height_cm > 0
            ),

        CONSTRAINT CK_OrderRecipeItems_Position
            CHECK (position_number > 0)
    );
END;
GO


-- =========================================================
-- POWIĄZANIE SNAPSHOTU SKŁADNIKA Z KONKRETNĄ POZYCJĄ
-- Stare rekordy pozostaną z wartością NULL.
-- =========================================================

IF COL_LENGTH(
    'dbo.OrderIngredients',
    'order_recipe_item_id'
) IS NULL
BEGIN
    ALTER TABLE dbo.OrderIngredients
    ADD order_recipe_item_id INT NULL;
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_keys
    WHERE name =
        'FK_OrderIngredients_OrderRecipeItems'
)
BEGIN
    ALTER TABLE dbo.OrderIngredients
    ADD CONSTRAINT
        FK_OrderIngredients_OrderRecipeItems
    FOREIGN KEY (order_recipe_item_id)
    REFERENCES dbo.OrderRecipeItems(
        order_recipe_item_id
    );
END;
GO


-- =========================================================
-- INDEKSY
-- =========================================================

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_OrderRecipeItems_OrderId'
        AND object_id =
            OBJECT_ID('dbo.OrderRecipeItems')
)
BEGIN
    CREATE INDEX IX_OrderRecipeItems_OrderId
    ON dbo.OrderRecipeItems(order_id);
END;
GO


IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE
        name =
            'IX_OrderIngredients_OrderRecipeItemId'
        AND object_id =
            OBJECT_ID('dbo.OrderIngredients')
)
BEGIN
    CREATE INDEX
        IX_OrderIngredients_OrderRecipeItemId
    ON dbo.OrderIngredients(order_recipe_item_id);
END;
GO


-- =========================================================
-- KONTROLA
-- =========================================================

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN (
    'OrderRecipeItems',
    'OrderIngredients'
)
ORDER BY
    TABLE_NAME,
    ORDINAL_POSITION;
GO