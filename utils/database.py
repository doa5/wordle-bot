from discord.ext import commands
import logging
import sqlite3

class DatabaseCog(commands.Cog):
    """
    Cog to manage database connections and operations.
    """
    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the DatabaseCog with bot instance."""
        self.bot = bot
        self.database_path = 'wordle_scores.db'
        self.connection = None
        self.connect_to_database()

    def connect_to_database(self) -> None:
        """Establish a connection to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.database_path)
            logging.info(f"Connected to database at {self.database_path}")
            self.create_tables()
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            self.connection = None

    def create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        if not self.connection:
            logging.error("No database connection.")
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wordle_scores (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT,
                    score INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.connection.commit()
            logging.info("Database tables ensured.")
        except sqlite3.Error as e:
            logging.error(f"Error creating tables: {e}")
            self.connection = None
    
    def close_connection(self) -> None:
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed.")

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Execute a SQL query and return the results.
        
        Args:
            query: The SQL query to execute.
            params: Optional parameters for the SQL query.
                   Common examples:
                   - Single value: (user_id,)
                   - Multiple values: (user_id, username, score, date)
                   - Date range: ("2024-01-01", "2024-01-31")
                   - User list: (123456, 789012, 345678)
        
        Returns:
            List of tuples containing the query results.
        """
        if not self.connection:
            logging.error("No database connection.")
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            self.connection.commit()
            logging.info(f"Executed query: {query} with params: {params}")
            return results
        except sqlite3.Error as e:
            logging.error(f"Database query error: {e}")
            return []

    def save_wordle_score(self, user_id: int, username: str, score: int, date: str) -> bool:
        """
        Save a Wordle score to the database.

        Args:
            user_id: Discord user ID.
            username: Discord username.
            score: Number of attempts (1-6) or 8 for failure.
            date: Date when the report was processed (YYYY-MM-DD format).
                  * NOTE: Bot processes at 00:20, so this represents the day
                  * the report was received, not necessarily the puzzle date.

        Returns:
            True if the score was saved successfully, False otherwise.
        """
        
        query = """INSERT OR REPLACE INTO wordle_scores 
                   (user_id, username, score, date) 
                   VALUES (?, ?, ?, ?)"""
        params = (user_id, username, score, date)
        logging.info(f"Saving score for user {username} ({user_id}): {score} on {date}")
        result = self.execute_query(query, params)
        return len(result) == 0
    
    def has_duplicate_submission(self, user_id: int, date: str) -> bool:
        """Check if a user has already submitted a score for a specific date.

        Args:
            user_id (int): The ID of the user.
            date (str): The date to check (YYYY-MM-DD format).

        Returns:
            bool: True if a duplicate submission exists, False otherwise.
        """
        query = "SELECT id FROM wordle_scores WHERE user_id = ? AND date = ?"
        params = (user_id, date)
        logging.info(f"Checking for duplicate submission for user {user_id} on {date}")
        result = self.execute_query(query, params)
        logging.info(f"Duplicate submission check result: {bool(result)}")
        return bool(result)

    @commands.Cog.listener()
    async def on_cog_unload(self) -> None:
        """Ensure the database connection is closed when the cog is unloaded."""
        self.close_connection()

async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(DatabaseCog(bot))
    logging.info("DatabaseCog has been added to bot.")