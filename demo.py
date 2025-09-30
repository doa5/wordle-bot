#!/usr/bin/env python3
"""Demo script to show how the Wordle bot processes messages."""

from parser import parse_wordle_score
from database import WordleDatabase
import os
import tempfile

def demo():
    """Demonstrate the Wordle bot functionality."""
    
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = WordleDatabase(db_path)
        
        print("=" * 70)
        print("WORDLE BOT DEMO")
        print("=" * 70)
        
        # Sample messages
        sample_messages = [
            "Wordle 1,234 4/6\n⬛⬛🟨⬛⬛\n🟨🟩⬛⬛⬛\n⬛🟩🟩🟩🟩\n🟩🟩🟩🟩🟩",
            "Wordle 1,234 3/6\n🟨⬛🟨⬛⬛\n⬛🟩🟩🟩🟩\n🟩🟩🟩🟩🟩",
            "Wordle 1,235 5/6\n⬛⬛⬛⬛🟨\n🟨⬛⬛⬛⬛\n⬛🟨🟨⬛⬛\n🟨🟩🟩🟩⬛\n🟩🟩🟩🟩🟩",
            "Wordle 1,235 X/6\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n⬛⬛🟨⬛⬛\n🟨⬛⬛⬛⬛\n⬛🟨⬛⬛⬛\n⬛🟨⬛⬛⬛",
        ]
        
        users = [
            ("user1", "Alice"),
            ("user2", "Bob"),
            ("user1", "Alice"),
            ("user3", "Charlie"),
        ]
        
        print("\n1. PROCESSING WORDLE MESSAGES")
        print("-" * 70)
        
        for i, (message, (user_id, username)) in enumerate(zip(sample_messages, users), 1):
            print(f"\nMessage {i} from {username}:")
            print(f"  {message.splitlines()[0]}")
            
            result = parse_wordle_score(message)
            if result:
                wordle_number, score = result
                score_text = "X" if score == 7 else str(score)
                print(f"  → Parsed: Wordle #{wordle_number}, Score: {score_text}/6")
                
                success = db.add_score(user_id, username, wordle_number, score)
                if success:
                    print(f"  ✅ Score recorded successfully!")
                else:
                    print(f"  ⚠️  Duplicate score (already recorded)")
        
        print("\n\n2. WEEKLY LEADERBOARD")
        print("-" * 70)
        
        leaderboard = db.get_weekly_leaderboard()
        
        for i, (username, avg_score, total_games) in enumerate(leaderboard, 1):
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
            
            print(f"{medal}{i}. {username}")
            print(f"   Average Score: {avg_score:.2f}")
            print(f"   Games Played: {total_games}")
            print()
        
        print("\n3. USER STATISTICS")
        print("-" * 70)
        
        for user_id, username in [("user1", "Alice"), ("user2", "Bob"), ("user3", "Charlie")]:
            stats = db.get_user_stats(user_id)
            if stats:
                _, avg_score, total_games = stats
                print(f"\n{username}'s Stats:")
                print(f"  Average Score: {avg_score:.2f}")
                print(f"  Total Games: {total_games}")
        
        print("\n" + "=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    demo()
