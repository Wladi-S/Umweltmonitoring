import pandas as pd
import psycopg2
from psycopg2 import sql

# Datenbank-Verbindungsdetails
DB_DETAILS = {
    "dbname": "Umweltmonitoring",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": 5432,
}


# Funktion zur Herstellung der Datenbankverbindung
def get_db_connection(dbname):
    return psycopg2.connect(
        dbname=dbname,
        user=DB_DETAILS["user"],
        password=DB_DETAILS["password"],
        host=DB_DETAILS["host"],
        port=DB_DETAILS["port"],
    )


# Kombinierte Funktion zum Abrufen und Pivotieren der Messdaten aus der Datenbank
def fetch_and_pivot_sensor_data(sensor_ids=None):
    conn = get_db_connection(DB_DETAILS["dbname"])
    cur = conn.cursor()

    if sensor_ids:
        query = sql.SQL(
            """
            SELECT s.title AS sensor_title, s.unit, s.sensor_id, m.created_at, m.value
            FROM measurement m
            JOIN sensor s ON m.sensor_id = s.sensor_id
            WHERE m.sensor_id = ANY(%s)
            ORDER BY m.created_at;
        """
        )
        cur.execute(query, (sensor_ids,))
    else:
        query = """
            SELECT s.title AS sensor_title, s.unit, s.sensor_id, m.created_at, m.value
            FROM measurement m
            JOIN sensor s ON m.sensor_id = s.sensor_id
            ORDER BY m.created_at;
        """
        cur.execute(query)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    df = pd.DataFrame(
        rows, columns=["sensor_title", "unit", "sensor_id", "created_at", "value"]
    )

    # Erstelle eine neue Spalte für den kombinierten Sensor-Titel und Einheit
    df["sensor_unit"] = df["sensor_title"] + " in " + df["unit"]

    # Pivotiere das DataFrame
    df_pivot = df.pivot(index="created_at", columns="sensor_unit", values="value")

    # Setze den Index zurück, um 'created_at' wieder als Spalte zu erhalten
    df_pivot.reset_index(inplace=True)

    return df_pivot


# Funktion zum Abrufen der Sensebox-Daten
def fetch_sensebox_info():
    conn = get_db_connection(DB_DETAILS["dbname"])
    cur = conn.cursor()

    query = """
        SELECT sensebox_id, name, created_at, description, exposure, last_measurement_at, latitude, longitude, altitude
        FROM sensebox;
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    columns = [
        "sensebox_id",
        "name",
        "created_at",
        "description",
        "exposure",
        "last_measurement_at",
        "latitude",
        "longitude",
        "altitude",
    ]
    df = pd.DataFrame(rows, columns=columns)
    return df


# Hauptprogramm
def main(sensor_ids=None):
    df_pivot = fetch_and_pivot_sensor_data(sensor_ids)
    print(df_pivot)


if __name__ == "__main__":
    # Beispielaufruf ohne Filter
    main()
