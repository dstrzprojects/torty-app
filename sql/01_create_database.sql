USE TortyDB;
GO

CREATE TABLE Ingredients (
    ingredient_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    package_quantity DECIMAL(10,2) NOT NULL,
    unit NVARCHAR(10) NOT NULL,          -- g, kg, ml, l, szt.
    package_price DECIMAL(10,2) NOT NULL,
    updated_at DATETIME2 DEFAULT SYSDATETIME()
);

CREATE TABLE Recipes (
    recipe_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    description NVARCHAR(500)
);

CREATE TABLE RecipeIngredients (
    recipe_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (recipe_id, ingredient_id),
    FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id),
    FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id)
);

CREATE TABLE CakeCosts (
    cost_id INT IDENTITY(1,1) PRIMARY KEY,
    recipe_id INT NOT NULL,
    work_hours DECIMAL(6,2) DEFAULT 0,
    hourly_rate DECIMAL(10,2) DEFAULT 0,
    utilities_cost DECIMAL(10,2) DEFAULT 0,
    equipment_depreciation DECIMAL(10,2) DEFAULT 0,
    additional_cost DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (recipe_id) REFERENCES Recipes(recipe_id)
);
GO