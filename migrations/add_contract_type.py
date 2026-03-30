#!/usr/bin/env python3
"""
Migration script to add contract_type column to listings table
"""

import sqlite3
import os

def add_contract_type_column():
    """Add contract_type column to listings table if it doesn't exist."""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'apartment_finder.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(listings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'contract_type' not in columns:
            print("Adding contract_type column to listings table...")
            cursor.execute("ALTER TABLE listings ADD COLUMN contract_type VARCHAR(20)")
            conn.commit()
            print("Column added successfully.")
        else:
            print("contract_type column already exists.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error adding contract_type column: {e}")
        return False

if __name__ == "__main__":
    add_contract_type_column()
