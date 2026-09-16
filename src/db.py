import pyodbc

CONNECTION_STRING = (
    r"DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=localhost\SQLEXPRESS;"
    r"DATABASE=TortyDB;"
    r"Trusted_Connection=yes;"
    r"TrustServerCertificate=yes;"
)


def get_connection():
    return pyodbc.connect(CONNECTION_STRING)