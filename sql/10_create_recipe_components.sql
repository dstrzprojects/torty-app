USE TortyDB;
GO

IF OBJECT_ID('dbo.RecipeComponents', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.RecipeComponents (
        parent_recipe_id INT NOT NULL,
        child_recipe_id INT NOT NULL,

        quantity_factor DECIMAL(10,3)
            NOT NULL
            CONSTRAINT DF_RecipeComponents_Factor
            DEFAULT 1,

        created_at DATETIME2
            NOT NULL
            CONSTRAINT DF_RecipeComponents_CreatedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT PK_RecipeComponents
            PRIMARY KEY (
                parent_recipe_id,
                child_recipe_id
            ),

        CONSTRAINT FK_RecipeComponents_ParentRecipe
            FOREIGN KEY (parent_recipe_id)
            REFERENCES dbo.Recipes(recipe_id),

        CONSTRAINT FK_RecipeComponents_ChildRecipe
            FOREIGN KEY (child_recipe_id)
            REFERENCES dbo.Recipes(recipe_id),

        CONSTRAINT CK_RecipeComponents_DifferentRecipes
            CHECK (
                parent_recipe_id <> child_recipe_id
            ),

        CONSTRAINT CK_RecipeComponents_FactorPositive
            CHECK (
                quantity_factor > 0
            )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_RecipeComponents_ChildRecipe'
      AND object_id = OBJECT_ID(
          'dbo.RecipeComponents'
      )
)
BEGIN
    CREATE INDEX IX_RecipeComponents_ChildRecipe
    ON dbo.RecipeComponents(child_recipe_id);
END;
GO