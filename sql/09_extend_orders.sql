USE TortyDB;
GO

SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;


    -- =====================================================
    -- 1. MIGAWKA NAZWY PRZEPISU
    -- =====================================================

    IF COL_LENGTH(
        'dbo.Orders',
        'recipe_name_snapshot'
    ) IS NULL
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD recipe_name_snapshot NVARCHAR(200) NULL;
        ';
    END;


    -- Uzupełnienie nazwy dla ewentualnych istniejących zamówień

    EXEC sys.sp_executesql N'
        UPDATE o
        SET recipe_name_snapshot = r.name
        FROM dbo.Orders AS o
        JOIN dbo.Recipes AS r
            ON r.recipe_id = o.recipe_id
        WHERE o.recipe_name_snapshot IS NULL;
    ';


    -- Zmiana kolumny na obowiązkową

    IF EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME = 'Orders'
          AND COLUMN_NAME = 'recipe_name_snapshot'
          AND IS_NULLABLE = 'YES'
    )
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ALTER COLUMN recipe_name_snapshot
                NVARCHAR(200) NOT NULL;
        ';
    END;


    -- =====================================================
    -- 2. CZAS PRACY
    -- =====================================================

    IF COL_LENGTH('dbo.Orders', 'work_hours') IS NULL
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD work_hours DECIMAL(6,2) NOT NULL
                CONSTRAINT DF_Orders_WorkHours
                DEFAULT 0;
        ';
    END;


    IF COL_LENGTH('dbo.Orders', 'hourly_rate') IS NULL
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD hourly_rate DECIMAL(10,2) NOT NULL
                CONSTRAINT DF_Orders_HourlyRate
                DEFAULT 0;
        ';
    END;


    -- =====================================================
    -- 3. ZALICZKA
    -- =====================================================

    IF COL_LENGTH('dbo.Orders', 'deposit_amount') IS NULL
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD deposit_amount DECIMAL(10,2) NOT NULL
                CONSTRAINT DF_Orders_Deposit
                DEFAULT 0;
        ';
    END;


    -- =====================================================
    -- 4. SPOSÓB ODBIORU
    -- =====================================================

    IF COL_LENGTH(
        'dbo.Orders',
        'fulfillment_method'
    ) IS NULL
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD fulfillment_method NVARCHAR(30) NOT NULL
                CONSTRAINT DF_Orders_Fulfillment
                DEFAULT N''Odbiór osobisty'';
        ';
    END;


    IF COL_LENGTH(
        'dbo.Orders',
        'delivery_address'
    ) IS NULL
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD delivery_address NVARCHAR(300) NULL;
        ';
    END;


    -- =====================================================
    -- 5. OGRANICZENIA CHECK
    -- Muszą być dynamiczne, ponieważ korzystają z nowych kolumn.
    -- =====================================================

    IF NOT EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE name = 'CK_Orders_Deposit_Nonnegative'
    )
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD CONSTRAINT CK_Orders_Deposit_Nonnegative
                CHECK (deposit_amount >= 0);
        ';
    END;


    IF NOT EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE name = 'CK_Orders_WorkValues_Nonnegative'
    )
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD CONSTRAINT CK_Orders_WorkValues_Nonnegative
                CHECK (
                    work_hours >= 0
                    AND hourly_rate >= 0
                );
        ';
    END;


    IF NOT EXISTS (
        SELECT 1
        FROM sys.check_constraints
        WHERE name = 'CK_Orders_FulfillmentMethod'
    )
    BEGIN
        EXEC sys.sp_executesql N'
            ALTER TABLE dbo.Orders
            ADD CONSTRAINT CK_Orders_FulfillmentMethod
                CHECK (
                    fulfillment_method IN (
                        N''Odbiór osobisty'',
                        N''Dostawa''
                    )
                );
        ';
    END;


    -- =====================================================
    -- 6. MIGAWKA SKŁADNIKÓW ZAMÓWIENIA
    -- =====================================================

    IF OBJECT_ID('dbo.OrderIngredients', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.OrderIngredients (
            order_ingredient_id INT IDENTITY(1,1)
                NOT NULL,

            order_id INT NOT NULL,

            ingredient_id INT NULL,

            ingredient_name_snapshot NVARCHAR(200)
                NOT NULL,

            scaled_quantity DECIMAL(12,2)
                NOT NULL,

            unit NVARCHAR(20)
                NOT NULL,

            package_quantity_snapshot DECIMAL(10,2)
                NULL,

            package_price_snapshot DECIMAL(10,2)
                NULL,

            ingredient_cost DECIMAL(10,2)
                NULL,

            CONSTRAINT PK_OrderIngredients
                PRIMARY KEY (order_ingredient_id),

            CONSTRAINT FK_OrderIngredients_Orders
                FOREIGN KEY (order_id)
                REFERENCES dbo.Orders(order_id)
                ON DELETE CASCADE,

            CONSTRAINT FK_OrderIngredients_Ingredients
                FOREIGN KEY (ingredient_id)
                REFERENCES dbo.Ingredients(ingredient_id),

            CONSTRAINT CK_OrderIngredients_QuantityPositive
                CHECK (scaled_quantity > 0),

            CONSTRAINT CK_OrderIngredients_CostNonnegative
                CHECK (
                    ingredient_cost IS NULL
                    OR ingredient_cost >= 0
                )
        );
    END;


    -- =====================================================
    -- 7. INDEKSY
    -- =====================================================

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Orders_Status_DueDate'
          AND object_id = OBJECT_ID('dbo.Orders')
    )
    BEGIN
        CREATE INDEX IX_Orders_Status_DueDate
        ON dbo.Orders (
            status,
            due_date
        );
    END;


    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_OrderIngredients_OrderId'
          AND object_id = OBJECT_ID('dbo.OrderIngredients')
    )
    BEGIN
        CREATE INDEX IX_OrderIngredients_OrderId
        ON dbo.OrderIngredients(order_id);
    END;


    COMMIT TRANSACTION;

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO


-- =========================================================
-- 8. KONTROLA WYNIKU
-- =========================================================

SELECT
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
  AND TABLE_NAME = 'Orders'
ORDER BY ORDINAL_POSITION;
GO


SELECT
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
  AND TABLE_NAME = 'OrderIngredients'
ORDER BY ORDINAL_POSITION;
GO