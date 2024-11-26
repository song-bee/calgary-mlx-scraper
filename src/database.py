import sqlite3

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to database: {db_file}")
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table(conn):
    """Create a table for storing property data."""
    try:
        sql_create_properties_table = """
        CREATE TABLE IF NOT EXISTS properties (
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

def update_price_differences(conn):
    """Update the price_difference and percent_difference columns in the properties table."""
    try:
        cursor = conn.cursor()
        
        # Update price_difference and percent_difference
        update_query = """
        UPDATE properties
        SET price_difference = sold_price - list_price,
            percent_difference = ROUND(((sold_price - list_price) / list_price) * 100, 2)
        WHERE list_price != 0;  -- Avoid division by zero
        """
        
        cursor.execute(update_query)
        conn.commit()
        print("Updated price_difference and percent_difference for existing records.")
    except sqlite3.Error as e:
        print(f"Error updating price differences: {e}")
