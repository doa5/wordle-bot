import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Optional


class WordleDatabase:
    def __init__(self, db_path: str = "wordle_scores.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                wordle_number INTEGER NOT NULL,
                score INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                UNIQUE(user_id, wordle_number)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_score(self, user_id: str, username: str, wordle_number: int, score: int) -> bool:
        """
        Add a Wordle score to the database.
        
        Args:
            user_id: Discord user ID
            username: Discord username
            wordle_number: Wordle puzzle number
            score: Number of guesses (1-6, or 7 for failed)
            
        Returns:
            True if score was added, False if it already exists
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO scores (user_id, username, wordle_number, score, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, wordle_number, score, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_weekly_leaderboard(self) -> List[Tuple[str, float, int]]:
        """
        Get the leaderboard for the current week.
        
        Returns:
            List of tuples (username, average_score, total_games)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate the start of the week (Monday)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        cursor.execute('''
            SELECT username, AVG(score) as avg_score, COUNT(*) as total_games
            FROM scores
            WHERE timestamp >= ?
            GROUP BY user_id
            ORDER BY avg_score ASC, total_games DESC
        ''', (start_of_week.isoformat(),))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

    def get_all_time_leaderboard(self) -> List[Tuple[str, float, int]]:
        """
        Get the all-time leaderboard.
        
        Returns:
            List of tuples (username, average_score, total_games)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, AVG(score) as avg_score, COUNT(*) as total_games
            FROM scores
            GROUP BY user_id
            ORDER BY avg_score ASC, total_games DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return results

    def get_user_stats(self, user_id: str) -> Optional[Tuple[str, float, int]]:
        """
        Get statistics for a specific user.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Tuple of (username, average_score, total_games) or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, AVG(score) as avg_score, COUNT(*) as total_games
            FROM scores
            WHERE user_id = ?
            GROUP BY user_id
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
