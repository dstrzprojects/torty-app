import pyodbc

connection_string = (
    r"DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=.\SQLEXPRESS;"
    r"DATABASE=TortyDB;"
    r"Trusted_Connection=yes;"
    r"TrustServerCertificate=yes;"
)

with pyodbc.connect(connection_string) as connection:
    cursor = connection.cursor()

    cursor.execute("""
        SELECT ingredient_id, name, package_quantity, unit, package_price
        FROM Ingredients
        ORDER BY name;
    """)

    for row in cursor.fetchall():
        print(
            row.ingredient_id,
            row.name,
            row.package_quantity,
            row.unit,
            row.package_price,
        )