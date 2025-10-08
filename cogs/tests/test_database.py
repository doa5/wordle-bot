import pytest
import sqlite3
import tempfile
import os
from unittest import mock
import sys
import types
import asyncio

# Create properly mocked discord modules
mock_discord = types.ModuleType('discord')
mock_discord.Embed = mock.MagicMock
mock_discord.ext = types.ModuleType('discord.ext')

mock_commands = types.ModuleType('discord.ext.commands')
mock_cog_class = mock.MagicMock()
mock_cog_class.listener = mock.MagicMock()
mock_commands.Cog = mock_cog_class
mock_commands.Bot = mock.MagicMock
mock_commands.Context = mock.MagicMock
mock_commands.command = mock.MagicMock()
mock_commands.is_owner = mock.MagicMock()

# Assign to sys.modules
sys.modules['discord'] = mock_discord
sys.modules['discord.ext'] = mock_discord.ext
sys.modules['discord.ext.commands'] = mock_commands

# Now import discord and our module
import discord
from discord.ext import commands
from cogs.database import DatabaseCog


@pytest.fixture
def mock_bot():
    bot = mock.Mock(spec=commands.Bot)
    bot.get_guild = mock.Mock(return_value=None)

    mock_loop = mock.Mock()
    mock_loop.create_task = mock.Mock(return_value=mock.Mock())
    bot.loop = mock_loop
    bot.is_closed = mock.Mock(return_value=False)
    return bot

@pytest.fixture
def db_cog(mock_bot):
    """Create a DatabaseCog with temporary database for testing. """
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_wordle_scores.db")
    
    cog = DatabaseCog(mock_bot)
    cog.database_path = temp_db_path
    cog.connection = sqlite3.connect(cog.database_path)
    cog.create_tables()
    
    yield cog
    
    cog.close_connection()
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
    os.rmdir(temp_dir)

def test_create_tables_creates_table(db_cog):
    """Test that the wordle_scores table is created properly."""
    cursor = db_cog.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wordle_scores'")
    assert cursor.fetchone() is not None

def test_save_wordle_score_and_query(db_cog):
    """Test saving a Wordle score and querying it back."""
    result = db_cog.save_wordle_score(123, 456, "tester", 4, "2024-06-01")
    assert result is True
    rows = db_cog.execute_query("SELECT * FROM wordle_scores WHERE user_id=? AND guild_id=?", (123, 456))
    assert len(rows) == 1
    assert rows[0][2] == "456"  # guild_id as TEXT

def test_save_wordle_score_returns_false_on_no_connection(mock_bot):
    """Test that save_wordle_score returns False when there is no database connection."""
    cog = DatabaseCog(mock_bot)
    cog.connection = None
    assert cog.save_wordle_score(1, 2, "user", 3, "2024-06-01") is False

def test_has_duplicate_submission(db_cog):
    """Test has_duplicate_submission method."""
    db_cog.save_wordle_score(111, 222, "user1", 2, "2024-06-02")
    assert db_cog.has_duplicate_submission(111, 222, "2024-06-02") is True
    assert db_cog.has_duplicate_submission(111, 222, "2024-06-03") is False

def test_execute_query_returns_empty_on_no_connection(mock_bot):
    """Test that execute_query returns empty list when there is no database connection."""
    cog = DatabaseCog(mock_bot)
    cog.connection = None
    result = cog.execute_query("SELECT 1")
    assert result == []

def test_execute_query_returns_empty_on_sql_error(db_cog):
    """Test that execute_query returns empty list on SQL error."""
    result = db_cog.execute_query("SELECT * FROM non_existent_table")
    assert result == []

def test_close_connection_closes(db_cog):
    """Test that close_connection properly closes the database connection."""
    conn = db_cog.connection
    db_cog.close_connection()
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")

def test_on_cog_unload_closes_connection(db_cog):
    """Test that on_cog_unload closes the database connection."""
    conn = db_cog.connection

    # Simulate async call
    asyncio.run(db_cog.on_cog_unload())
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
