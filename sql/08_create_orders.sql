USE TortyDB;
GO

IF OBJECT_ID('dbo.Orders', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Orders (
        order_id INT IDENTITY(1,1) PRIMARY KEY,

        recipe_id INT NOT NULL,

        customer_name NVARCHAR(150) NOT NULL,
        customer_phone NVARCHAR(30) NULL,

        target_diameter_cm DECIMAL(5,2) NOT NULL,
        target_height_cm DECIMAL(5,2) NOT NULL,
        correction_percent DECIMAL(5,2) NOT NULL
            CONSTRAINT DF_Orders_Correction DEFAULT 0,

        due_date DATETIME2 NOT NULL,

        status NVARCHAR(30) NOT NULL
            CONSTRAINT DF_Orders_Status DEFAULT N'Nowe',

        ingredients_cost DECIMAL(10,2) NOT NULL,
        work_cost DECIMAL(10,2) NOT NULL,
        utilities_cost DECIMAL(10,2) NOT NULL,
        depreciation_cost DECIMAL(10,2) NOT NULL,
        decorations_cost DECIMAL(10,2) NOT NULL,
        packaging_cost DECIMAL(10,2) NOT NULL,

        markup_percent DECIMAL(5,2) NOT NULL,
        total_cost DECIMAL(10,2) NOT NULL,
        selling_price DECIMAL(10,2) NOT NULL,

        notes NVARCHAR(1000) NULL,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_Orders_CreatedAt DEFAULT SYSDATETIME(),

        updated_at DATETIME2 NOT NULL
            CONSTRAINT DF_Orders_UpdatedAt DEFAULT SYSDATETIME(),

        CONSTRAINT FK_Orders_Recipes
            FOREIGN KEY (recipe_id)
            REFERENCES dbo.Recipes(recipe_id),

        CONSTRAINT CK_Orders_Diameter_Positive
            CHECK (target_diameter_cm > 0),

        CONSTRAINT CK_Orders_Height_Positive
            CHECK (target_height_cm > 0),

        CONSTRAINT CK_Orders_Costs_Nonnegative
            CHECK (
                ingredients_cost >= 0
                AND work_cost >= 0
                AND utilities_cost >= 0
                AND depreciation_cost >= 0
                AND decorations_cost >= 0
                AND packaging_cost >= 0
                AND total_cost >= 0
                AND selling_price >= 0
            ),

        CONSTRAINT CK_Orders_Status
            CHECK (
                status IN (
                    N'Nowe',
                    N'Potwierdzone',
                    N'W realizacji',
                    N'Gotowe',
                    N'Odebrane',
                    N'Anulowane'
                )
            )
    );
END;
GO

SELECT
    order_id,
    customer_name,
    due_date,
    status,
    selling_price
FROM dbo.Orders;
GO