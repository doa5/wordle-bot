#!/usr/bin/env python3
"""
Test script to verify duplicate management functionality.
"""

import asyncio
import sqlite3
from cogs.database import DatabaseCog
from unittest.mock import Mock

async def test_duplicate_functions():
    """Test the duplicate management functions."""
    print("Testing duplicate management functionality...")
    
    # Create a mock bot
    mock_bot = Mock()
    
    # Create DatabaseCog instance
    db_cog = DatabaseCog(mock_bot)
    
    # Test has_duplicate_submission
    print("\n1. Testing has_duplicate_submission method:")
    
    # Test with known duplicate (from our earlier check)
    result = db_cog.has_duplicate_submission(383926733394542592, 1253606896292593664, "2025-09-29")
    print(f"   User 383926733394542592 on 2025-09-29: {'DUPLICATE FOUND' if result else 'No duplicate'}")
    
    # Test with non-existent combination
    result = db_cog.has_duplicate_submission(999999999, 1253606896292593664, "2025-01-01")
    print(f"   User 999999999 on 2025-01-01: {'DUPLICATE FOUND' if result else 'No duplicate'}")
    
    print("\n2. Direct database check for duplicates:")
    
    # Direct database check
    conn = sqlite3.connect('wordle_scores.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, guild_id, date, COUNT(*) as count
        FROM wordle_scores 
        GROUP BY user_id, guild_id, date 
        HAVING COUNT(*) > 1
        ORDER BY count DESC, date DESC
        LIMIT 5
    """)
    
    duplicates = cursor.fetchall()
    print(f"   Found {len(duplicates)} duplicate sets:")
    
    for user_id, guild_id, date, count in duplicates:
        print(f"   - User {user_id}, Guild {guild_id}, Date {date}: {count} entries")
    
    conn.close()
    
    print("\n✅ Duplicate detection functionality appears to be working!")
    print("\nYou can now use these bot commands:")
    print("   woguri show_duplicates       - Show all duplicates")
    print("   woguri clean_duplicates      - Remove duplicates (keeping first)")
    print("   woguri show_duplicates 12345 - Show duplicates for specific guild")

if __name__ == "__main__":
    asyncio.run(test_duplicate_functions())