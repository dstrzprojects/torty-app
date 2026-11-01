# Wycena tortów

Lokalna aplikacja do zarządzania składnikami, tworzenia przepisów oraz obliczania kosztów wykonania tortów.

## Możliwości

- baza składników i cen opakowań,
- przepisy oraz podprzepisy,
- skalowanie receptur według średnicy i wysokości,
- szybka wycena kilku przepisów,
- pełna wycena z robocizną i kosztami dodatkowymi,
- ustalanie rzeczywistej ceny sprzedaży,
- zapisywanie i przeglądanie zamówień.

## Technologie

- Python
- Streamlit
- Microsoft SQL Server
- pyodbc
- Git

## Uruchomienie

Aplikację można uruchomić plikiem:

```text
uruchom_torty.bat
```

lub poleceniem:

```powershell
venv\Scripts\python.exe -m streamlit run src\app.py
```

SQL Server musi być uruchomiony. Ustawienia połączenia znajdują się w `src/db.py`.

## Instalacja

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

Następnie należy uruchomić skrypty z folderu `sql` w odpowiedniej kolejności.

## Dane

Aplikacja korzysta z lokalnej bazy SQL Server. Przepisy, ceny i zamówienia nie są przechowywane w repozytorium Git.

Projekt jest rozwijany jako praktyczna aplikacja do nauki Pythona, SQL i projektowania baz danych.