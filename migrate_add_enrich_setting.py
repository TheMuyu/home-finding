#!/usr/bin/env python3
"""
Add enrich_all_even_if_cached column to user_settings table.
Run this once to migrate the database.
"""
import sqlite3
import sys

def migrate():
    try:
        conn = sqlite3.connect('database/apartment_finder.db')
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'enrich_all_even_if_cached' in columns:
            print("Column 'enrich_all_even_if_cached' already exists.")
            return
        
        # Add the column
        cursor.execute("""
            ALTER TABLE user_settings 
            ADD COLUMN enrich_all_even_if_cached BOOLEAN DEFAULT 0
        """)
        
        conn.commit()
        print("✅ Added enrich_all_even_if_cached column to user_settings table.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate()
