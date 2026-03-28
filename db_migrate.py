"""
Run this once to add new columns to the existing database without losing data.
Usage:  python db_migrate.py
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__),
                       "database", "apartment_finder.db")

NEW_COLUMNS = [
    ("listings", "amenities",           "TEXT DEFAULT '[]'"),
    # (table, column_name, sql_type_with_default)
    ("listings", "available_until",      "TEXT"),
    ("listings", "home_type",            "TEXT"),
    ("listings", "furnishing",           "TEXT"),
    ("listings", "is_shared",            "BOOLEAN"),
    ("listings", "service_fee_sek",      "INTEGER"),
    ("listings", "electricity_included", "BOOLEAN"),
    ("listings", "deposit_months",       "INTEGER"),
    ("listings", "house_rules",          "TEXT DEFAULT '{}'"),
    ("listings", "transit_route",        "TEXT DEFAULT '{}'"),
]

conn = sqlite3.connect(DB_PATH)
for table, col, col_type in NEW_COLUMNS:
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        print(f"  + added {col}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"  ~ {col} already exists")
        else:
            raise
conn.commit()
conn.close()
print("Migration complete.")
