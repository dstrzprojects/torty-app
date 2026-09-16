USE TortyDB;
GO

ALTER TABLE dbo.Ingredients
ALTER COLUMN package_quantity DECIMAL(10,2) NULL;
GO

ALTER TABLE dbo.Ingredients
ALTER COLUMN package_price DECIMAL(10,2) NULL;
GO