#!/usr/bin/env python3
"""Tests for the database module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import tempfile
from database import WordleDatabase


def test_database():
    """Test the database functionality."""
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        print(f"Testing database at {db_path}...")
        db = WordleDatabase(db_path)
        
        # Test adding scores
        print("\n1. Testing add_score()...")
        assert db.add_score("user1", "Alice", 1234, 4), "Should add first score"
        print("✓ Added score for Alice (Wordle 1234, score 4)")
        
        assert db.add_score("user2", "Bob", 1234, 3), "Should add score for different user"
        print("✓ Added score for Bob (Wordle 1234, score 3)")
        
        assert not db.add_score("user1", "Alice", 1234, 5), "Should reject duplicate"
        print("✓ Rejected duplicate score for Alice (Wordle 1234)")
        
        assert db.add_score("user1", "Alice", 1235, 5), "Should add different Wordle number"
        print("✓ Added score for Alice (Wordle 1235, score 5)")
        
        # Test weekly leaderboard
        print("\n2. Testing get_weekly_leaderboard()...")
        leaderboard = db.get_weekly_leaderboard()
        print(f"✓ Got {len(leaderboard)} entries")
        for username, avg_score, total_games in leaderboard:
            print(f"  - {username}: avg={avg_score:.2f}, games={total_games}")
        
        assert len(leaderboard) == 2, "Should have 2 users"
        assert leaderboard[0][0] == "Bob", "Bob should be first (lower avg)"
        assert leaderboard[0][1] == 3.0, "Bob's average should be 3.0"
        assert leaderboard[1][0] == "Alice", "Alice should be second"
        assert leaderboard[1][1] == 4.5, "Alice's average should be 4.5"
        
        # Test all-time leaderboard
        print("\n3. Testing get_all_time_leaderboard()...")
        all_time = db.get_all_time_leaderboard()
        assert len(all_time) == 2, "Should have 2 users in all-time"
        print(f"✓ Got {len(all_time)} entries")
        
        # Test user stats
        print("\n4. Testing get_user_stats()...")
        alice_stats = db.get_user_stats("user1")
        assert alice_stats is not None, "Should find Alice's stats"
        username, avg_score, total_games = alice_stats
        assert username == "Alice", "Username should be Alice"
        assert avg_score == 4.5, "Average should be 4.5"
        assert total_games == 2, "Total games should be 2"
        print(f"✓ Alice stats: avg={avg_score:.2f}, games={total_games}")
        
        nonexistent_stats = db.get_user_stats("user999")
        assert nonexistent_stats is None, "Should return None for nonexistent user"
        print("✓ Returns None for nonexistent user")
        
        # Test failed attempts (X/6 = score 7)
        print("\n5. Testing failed attempts...")
        assert db.add_score("user3", "Charlie", 1234, 7), "Should add failed score"
        print("✓ Added failed attempt for Charlie (Wordle 1234, score 7/X)")
        
        charlie_stats = db.get_user_stats("user3")
        assert charlie_stats[1] == 7.0, "Failed attempt should count as 7"
        print(f"✓ Charlie stats: avg={charlie_stats[1]:.2f}")
        
        print("\n✅ All database tests passed!")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"\nCleaned up test database: {db_path}")


if __name__ == "__main__":
    test_database()
