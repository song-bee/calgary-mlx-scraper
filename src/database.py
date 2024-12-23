import sqlite3
from sqlite3 import Error
from typing import Optional


def create_connection(db_file: str) -> sqlite3.Connection:
    """Create a database connection"""
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        raise


def create_area_coordinates_table(conn: sqlite3.Connection) -> None:
    """Create the area coordinates table if it doesn't exist"""
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS area_coordinates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_name TEXT NOT NULL,
            area_code TEXT,
            city TEXT NOT NULL,
            province TEXT NOT NULL,
            country TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(area_name, city, province, country)
        );
        """
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
    except Error as e:
        print(f"Error creating area_coordinates table: {e}")
        raise


def get_area_coordinates(
    conn: sqlite3.Connection, area_name: str, city: str, province: str, country: str
) -> Optional[tuple]:
    """Get coordinates for an area from the database"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT latitude, longitude 
            FROM area_coordinates 
            WHERE area_name = ? AND city = ? AND province = ? AND country = ?
        """,
            (area_name, city, province, country),
        )
        result = cursor.fetchone()
        return result if result else None
    except Error as e:
        print(f"Error retrieving coordinates: {e}")
        return None


def save_area_coordinates(
    conn: sqlite3.Connection,
    area_name: str,
    area_code: str,
    city: str,
    province: str,
    country: str,
    latitude: float,
    longitude: float,
) -> None:
    """Save or update area coordinates in the database"""
    try:
        cursor = conn.cursor()
        sql = """
        INSERT INTO area_coordinates (area_name, area_code, city, province, country, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(area_name, city, province, country) 
        DO UPDATE SET 
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            last_updated = CURRENT_TIMESTAMP
        """
        cursor.execute(
            sql, (area_name, area_code, city, province, country, latitude, longitude)
        )
        conn.commit()
    except Error as e:
        print(f"Error saving coordinates: {e}")
        raise


def create_property_table(conn: sqlite3.Connection, table_name: str) -> None:
    """Create a table for storing property data."""
    try:
        sql_create_properties_table = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY,
            built_year INTEGER,
            street_number TEXT,
            street_name TEXT,
            street_direction TEXT,
            street_type TEXT,
            city TEXT,
            postal_code TEXT,
            latitude REAL,
            longitude REAL,
            square_feet REAL,
            avg_ft_price REAL,
            list_price REAL,
            sold_price REAL,
            price_difference REAL,
            percent_difference REAL,
            list_date TEXT,
            sold_date TEXT,
            mls_number TEXT,
            bedrooms INTEGER,
            bathrooms INTEGER,
            agent TEXT,
            office TEXT,
            neighborhood TEXT,
            detail_url TEXT,
            fetch_date DATE
        );
        """
        cursor = conn.cursor()
        cursor.execute(sql_create_properties_table)
        print("Properties table created.")
    except sqlite3.Error as e:
        print(e)


def update_price_differences(conn, table_name):
    """Update the price_difference and percent_difference columns in the properties table."""
    try:
        cursor = conn.cursor()

        # Update price_difference and percent_difference
        update_query = f"""
        UPDATE {table_name}
        SET price_difference = sold_price - list_price,
            percent_difference = ROUND(((sold_price - list_price) / list_price) * 100, 2)
        WHERE list_price != 0;  -- Avoid division by zero
        """

        cursor.execute(update_query)
        conn.commit()
        print("Updated price_difference and percent_difference for existing records.")
    except sqlite3.Error as e:
        print(f"Error updating price differences: {e}")
