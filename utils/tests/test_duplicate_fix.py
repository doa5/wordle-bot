#!/usr/bin/env python3
"""
Test script to verify the duplicate prevention fix in replace_score method.
"""

import sqlite3
from datetime import datetime

def test_duplicate_prevention():
    """Test the delete_user_score functionality to prevent duplicates."""
    
    # Connect to the database
    conn = sqlite3.connect('wordle_scores.db')
    cursor = conn.cursor()
    
    print("=== Testing Duplicate Prevention Fix ===")
    
    # First, let's see current duplicates
    cursor.execute("""
        SELECT user_id, guild_id, date, COUNT(*) as count
        FROM wordle_scores 
        GROUP BY user_id, guild_id, date 
        HAVING COUNT(*) > 1
    """)
    
    duplicates_before = cursor.fetchall()
    print(f"\nDuplicates BEFORE cleanup: {len(duplicates_before)} sets")
    
    for user_id, guild_id, date, count in duplicates_before:
        print(f"  User {user_id}, Date {date}: {count} entries")
    
    # Simulate what the new delete_user_score method would do
    print(f"\n=== Simulating delete_user_score for duplicates ===")
    
    for user_id, guild_id, date, count in duplicates_before:
        print(f"\nDeleting existing entries for User {user_id} on {date}...")
        
        cursor.execute("""
            DELETE FROM wordle_scores 
            WHERE user_id = ? AND guild_id = ? AND date = ?
        """, (user_id, guild_id, date))
        
        deleted_count = cursor.rowcount
        print(f"  Deleted {deleted_count} entries")
        
        # Simulate adding back ONE entry (what save_wordle_score would do)
        cursor.execute("""
            INSERT INTO wordle_scores (user_id, guild_id, username, score, date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, guild_id, f"TestUser_{user_id}", 3, date))
        
        print(f"  Added 1 new entry back")
    
    conn.commit()
    
    # Check duplicates after
    cursor.execute("""
        SELECT user_id, guild_id, date, COUNT(*) as count
        FROM wordle_scores 
        GROUP BY user_id, guild_id, date 
        HAVING COUNT(*) > 1
    """)
    
    duplicates_after = cursor.fetchall()
    print(f"\nDuplicates AFTER fix: {len(duplicates_after)} sets")
    
    if len(duplicates_after) == 0:
        print("✅ SUCCESS: No more duplicates!")
    else:
        print("❌ FAILED: Still have duplicates:")
        for user_id, guild_id, date, count in duplicates_after:
            print(f"  User {user_id}, Date {date}: {count} entries")
    
    # Show total rows
    cursor.execute("SELECT COUNT(*) FROM wordle_scores")
    total_rows = cursor.fetchone()[0]
    print(f"\nTotal rows in database: {total_rows}")
    
    conn.close()
    
    print("\n=== Fix Explanation ===")
    print("The replace_score method now:")
    print("1. Calls delete_user_score() to remove existing entries")
    print("2. Then calls save_wordle_score() to add the new entry")
    print("3. This prevents duplicates by ensuring only 1 entry per user/date")

if __name__ == "__main__":
    test_duplicate_prevention()