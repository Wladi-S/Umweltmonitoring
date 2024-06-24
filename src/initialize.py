import requests
import pandas as pd
import io
import psycopg2
from psycopg2 import sql
from time import time
from datetime import datetime, timezone

# Datenbank-Verbindungsdetails
DB_DETAILS = {
    "dbname": "Umweltmonitoring",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": 5432,
}


# Funktion zum Abrufen der Sensortitel und IDs
def get_sensor_titles_and_ids(sensebox_id):
    url = f"https://api.opensensemap.org/boxes/{sensebox_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [
            {"id": sensor["_id"], "title": sensor["title"]}
            for sensor in data["sensors"]
        ]
    else:
        print(f"Fehler beim Abrufen der Sensor-Titel: {response.status_code}")
        return []


# Funktion zum Abrufen der Sensordaten
def fetch_sensor_data(sensebox_id, sensor_title, start_date, end_date):
    url = "https://api.opensensemap.org//boxes/data"
    params = {
        "boxid": sensebox_id,
        "columns": "unit,value,createdAt",
        "download": "true",
        "format": "csv",
        "from-date": start_date,
        "phenomenon": sensor_title,
        "to-date": end_date,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.content.decode("utf-8")
    else:
        print(
            f"Fehler beim Herunterladen der CSV-Datei für {sensor_title}. Statuscode: {response.status_code}"
        )
        return ""


# Funktion zur Herstellung der Datenbankverbindung
def get_db_connection(dbname):
    return psycopg2.connect(
        dbname=dbname,
        user=DB_DETAILS["user"],
        password=DB_DETAILS["password"],
        host=DB_DETAILS["host"],
        port=DB_DETAILS["port"],
    )


# Funktion zum Erstellen der Datenbank, falls sie nicht existiert
def create_database():
    conn = get_db_connection("postgres")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_DETAILS["dbname"],))
    exists = cur.fetchone()
    if not exists:
        cur.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_DETAILS["dbname"]))
        )
        print(
            f"\nDatenbank '{DB_DETAILS['dbname']}' existiert nicht.\nProjekt wird initialisiert..\nDatenbank wird angelegt.."
        )
    cur.close()
    conn.close()


# Funktion zum Erstellen der Tabellen
def create_tables(cur):
    create_tables_query = """
    CREATE TABLE IF NOT EXISTS sensebox (
        sensebox_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(255),
        created_at TIMESTAMP,
        description TEXT,
        exposure VARCHAR(50),
        last_measurement_at TIMESTAMP,
        latitude DECIMAL(9, 6),
        longitude DECIMAL(9, 6),
        altitude DECIMAL(5, 2)
    );

    CREATE TABLE IF NOT EXISTS sensor (
        sensor_id VARCHAR(50) PRIMARY KEY,
        sensebox_id VARCHAR(50),
        title VARCHAR(255),
        unit VARCHAR(50),
        sensor_type VARCHAR(255),
        icon VARCHAR(255),
        FOREIGN KEY (sensebox_id) REFERENCES sensebox(sensebox_id)
    );

    CREATE TABLE IF NOT EXISTS measurement (
        measurement_id SERIAL PRIMARY KEY,
        sensor_id VARCHAR(50),
        created_at TIMESTAMP,
        value DECIMAL(10, 2),
        FOREIGN KEY (sensor_id) REFERENCES sensor(sensor_id),
        UNIQUE (sensor_id, created_at)
    );
    """
    cur.execute(create_tables_query)
    print(f"Tabellen werden angelegt..")


# Funktion zum Einfügen der Sensebox-Daten
def insert_sensebox_data(cur, sensebox):
    insert_sensebox_query = """
    INSERT INTO sensebox (
        sensebox_id, name, created_at, description, exposure, 
        last_measurement_at, latitude, longitude, altitude
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (sensebox_id) DO NOTHING;
    """
    sensebox_data = (
        sensebox["_id"],
        sensebox["name"],
        sensebox["createdAt"],
        sensebox["description"],
        sensebox["exposure"],
        sensebox["lastMeasurementAt"],
        sensebox["currentLocation"]["coordinates"][1],
        sensebox["currentLocation"]["coordinates"][0],
        sensebox["currentLocation"]["coordinates"][2],
    )
    cur.execute(insert_sensebox_query, sensebox_data)


# Funktion zum Einfügen der Sensor-Daten
def insert_sensor_data(cur, sensebox):
    insert_sensor_query = """
    INSERT INTO sensor (
        sensor_id, sensebox_id, title, unit, sensor_type, icon
    ) VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (sensor_id) DO NOTHING;
    """
    for sensor in sensebox["sensors"]:
        sensor_data = (
            sensor["_id"],
            sensebox["_id"],
            sensor["title"],
            sensor["unit"],
            sensor["sensorType"],
            sensor["icon"],
        )
        cur.execute(insert_sensor_query, sensor_data)


# Funktion zum Einfügen der Messdaten
def insert_measurement_data(cur, sensor, df):
    insert_measurement_query = """
    INSERT INTO measurement (sensor_id, created_at, value) VALUES (%s, %s, %s)
    ON CONFLICT (sensor_id, created_at) DO NOTHING;
    """
    for index, row in df.iterrows():
        cur.execute(
            insert_measurement_query,
            (sensor.get("id"), row["createdAt"], row[sensor.get("title")]),
        )


def update_last_measurement_at(cur):
    update_query = """
    UPDATE sensebox
    SET last_measurement_at = subquery.last_measurement_at
    FROM (
        SELECT s.sensebox_id, MAX(m.created_at) AS last_measurement_at
        FROM sensor s
        JOIN measurement m ON s.sensor_id = m.sensor_id
        GROUP BY s.sensebox_id
    ) AS subquery
    WHERE sensebox.sensebox_id = subquery.sensebox_id;
    """
    cur.execute(update_query)
    print("Last measurement dates updated.")


# Funktion zum Abrufen des letzten Messdatums eines Sensors
def get_last_measurement_date(cur, sensor_id):
    query = """
    SELECT MAX(created_at) FROM measurement WHERE sensor_id = %s;
    """
    cur.execute(query, (sensor_id,))
    result = cur.fetchone()
    return result[0] if result[0] else None


# Funktion zum Aktualisieren der Datenbank mit neuen Sensordaten
def update_data():
    # Verbindung zur spezifischen Datenbank herstellen
    conn = get_db_connection(DB_DETAILS["dbname"])
    conn.autocommit = True
    cur = conn.cursor()

    # Aktuelles Datum und Uhrzeit in ISO 8601 Format mit Zulu-Zeit
    end_date = (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )

    sensor_titles_and_ids = get_sensor_titles_and_ids("6252afcfd7e732001bb6b9f7")

    print(f"Sensor Informationen werden abgerufen..")

    for sensor in sensor_titles_and_ids:
        start_date = get_last_measurement_date(cur, sensor.get("id"))
        if not start_date:
            start_date = "2022-01-01T00:00:00.000Z"
        else:
            # Konvertiere start_date ins gewünschte Format
            start_date = (
                start_date.replace(tzinfo=timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )

        csv_data = fetch_sensor_data(
            "6252afcfd7e732001bb6b9f7", sensor.get("title"), start_date, end_date
        )
        if csv_data:
            df = pd.read_csv(io.StringIO(csv_data), usecols=["value", "createdAt"])
            df = df.rename(columns={"value": sensor.get("title")})
            df["createdAt"] = pd.to_datetime(df["createdAt"])
            if df["createdAt"].dt.tz is None:
                df["createdAt"] = df["createdAt"].dt.tz_localize("UTC", ambiguous="NaT")
            df["createdAt"] = df["createdAt"].dt.tz_convert("Europe/Berlin")
            df["createdAt"] = (
                df["createdAt"]
                .dt.tz_localize(None)
                .dt.tz_localize("Europe/Berlin", ambiguous="NaT")
            )
            df = df.dropna(subset=["createdAt"])
            df["createdAt"] = df["createdAt"].dt.floor("min")
            df.sort_values("createdAt", inplace=True)

            insert_measurement_data(cur, sensor, df)
            print(
                f"Alle Daten ab dem {start_date.replace('T', ' ').split('.')[0]} für Sensor {sensor.get('title')} wurden erfolgreich in die Datenbank eingefügt."
            )
    update_last_measurement_at(cur)
    cur.close()
    conn.close()


# Hauptprogramm
def main():
    # Sensebox URL
    sensebox_url = "https://api.opensensemap.org/boxes/6252afcfd7e732001bb6b9f7"

    # Datenbank erstellen, falls nicht vorhanden
    create_database()

    # Verbindung zur spezifischen Datenbank herstellen
    conn = get_db_connection(DB_DETAILS["dbname"])
    conn.autocommit = True
    cur = conn.cursor()

    # Prüfen, ob die Datenbank bereits existiert
    cur.execute("SELECT to_regclass('public.sensebox')")
    db_exists = cur.fetchone()[0] is not None

    if not db_exists:
        # Tabellen erstellen, falls sie nicht existieren
        create_tables(cur)

        # Abrufen der Sensebox-Daten
        response = requests.get(sensebox_url)
        sensebox = response.json()

        # Sensebox-Daten einfügen
        insert_sensebox_data(cur, sensebox)

        # Sensor-Daten einfügen
        insert_sensor_data(cur, sensebox)

        print(
            f"Sensebox Informationen für '{sensebox['name']}' wurden erfolgreich in die Datenbank eingefügt."
        )

    # Aktualisieren Sie die Datenbank mit neuen Sensordaten
    update_data()

    # Verbindung schließen
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
