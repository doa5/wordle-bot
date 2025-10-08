import pytest
import tempfile
import os
import sqlite3
from unittest import mock
import asyncio

# Import the actual modules (no mocking needed like other tests)
from cogs.database import DatabaseCog


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot for testing."""
    bot = mock.AsyncMock()
    bot.get_guild = mock.Mock(return_value=None)
    
    mock_loop = mock.Mock()
    mock_task = mock.Mock()
    mock_task.done = mock.Mock(return_value=False)
    mock_task.cancel = mock.Mock()
    mock_loop.create_task = mock.Mock(return_value=mock_task)
    bot.loop = mock_loop
    bot.is_closed = mock.Mock(return_value=False)
    return bot


@pytest.fixture
def db_cog(mock_bot):
    """Create a DatabaseCog with temporary database for testing."""
    # Create temporary database file
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_wordle_scores.db")
    
    # Create cog with temporary database
    cog = DatabaseCog(mock_bot)
    cog.database_path = temp_db_path
    cog.connection = sqlite3.connect(cog.database_path)
    cog.create_tables()
    
    yield cog
    
    # Cleanup
    cog.close_connection()
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
    os.rmdir(temp_dir)


def test_create_tables_creates_wordle_scores_table(db_cog):
    """Test that the wordle_scores table is created properly."""
    cursor = db_cog.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wordle_scores'")
    table = cursor.fetchone()
    assert table is not None
    assert table[0] == 'wordle_scores'


def test_save_wordle_score_success(db_cog):
    """Test saving a Wordle score successfully."""
    result = db_cog.save_wordle_score(
        user_id=12345, 
        guild_id=67890, 
        username="test_user", 
        score=4, 
        date="2024-06-01"
    )
    assert result is True


def test_save_wordle_score_and_retrieve(db_cog):
    """Test saving and then retrieving a Wordle score."""
    # Save a score
    db_cog.save_wordle_score(123, 456, "tester", 4, "2024-06-01")
    
    # Query it back
    rows = db_cog.execute_query(
        "SELECT * FROM wordle_scores WHERE user_id=? AND guild_id=?", 
        (123, 456)
    )
    
    assert len(rows) == 1
    row = rows[0]
    assert row[1] == "123"  # user_id as TEXT
    assert row[2] == "456"  # guild_id as TEXT
    assert row[3] == "tester"  # username
    assert row[4] == 4  # score
    assert row[5] == "2024-06-01"  # date


def test_save_wordle_score_no_connection(mock_bot):
    """Test saving fails gracefully when no database connection."""
    cog = DatabaseCog(mock_bot)
    cog.connection = None
    
    result = cog.save_wordle_score(1, 2, "user", 3, "2024-06-01")
    assert result is False


def test_has_duplicate_submission_true(db_cog):
    """Test duplicate detection returns True for existing submission."""
    # Save a score first
    db_cog.save_wordle_score(111, 222, "user1", 2, "2024-06-02")
    
    has_duplicate = db_cog.has_duplicate_submission(111, 222, "2024-06-02")
    assert has_duplicate is True


def test_has_duplicate_submission_false(db_cog):
    """Test duplicate detection returns False for non-existing submission."""
    has_duplicate = db_cog.has_duplicate_submission(111, 222, "2024-06-03")
    assert has_duplicate is False


def test_execute_query_no_connection(mock_bot):
    """Test execute_query returns empty list when no connection."""
    cog = DatabaseCog(mock_bot)
    cog.connection = None
    
    result = cog.execute_query("SELECT 1")
    assert result == []


def test_execute_query_sql_error(db_cog):
    """Test execute_query handles SQL errors gracefully."""
    result = db_cog.execute_query("SELECT * FROM non_existent_table")
    assert result == []


def test_close_connection(db_cog):
    """Test that closing connection prevents further queries."""
    conn = db_cog.connection
    db_cog.close_connection()
    
    # Trying to use closed connection should raise error
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


@pytest.mark.asyncio
async def test_on_cog_unload_closes_connection(db_cog):
    """Test that cog unload properly closes database connection."""
    conn = db_cog.connection
    
    await db_cog.on_cog_unload()
    
    # Connection should now be closed
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


@pytest.mark.asyncio
async def test_db_stats_command(db_cog):
    """Test db_stats command returns proper statistics."""
    db_cog.save_wordle_score(1, 100, "userA", 3, "2024-06-01")
    db_cog.save_wordle_score(2, 100, "userB", 4, "2024-06-02")
    db_cog.save_wordle_score(3, 200, "userC", 2, "2024-06-03")

    ctx = mock.AsyncMock()
    ctx.guild.id = 100
    
    await db_cog.db_stats.callback(db_cog, ctx)
    
    ctx.send.assert_called_once()
    args, kwargs = ctx.send.call_args
    
    # The embed is passed as keyword argument: ctx.send(embed=embed)
    embed = kwargs['embed']
    
    assert hasattr(embed, 'title')
    assert embed.title == "Database Statistics"


@pytest.mark.asyncio
async def test_db_guilds_command(db_cog):
    """Test db_guilds command lists server information."""
    db_cog.save_wordle_score(1, 100, "userA", 3, "2024-06-01")
    db_cog.save_wordle_score(2, 100, "userB", 4, "2024-06-02")  
    db_cog.save_wordle_score(3, 200, "userC", 2, "2024-06-03")

    ctx = mock.AsyncMock()
    
    await db_cog.db_guilds.callback(db_cog, ctx)
    
    ctx.send.assert_called_once()
    args, kwargs = ctx.send.call_args
    
    # The embed is passed as keyword argument: ctx.send(embed=embed)
    embed = kwargs['embed']
    
    assert hasattr(embed, 'title')
    assert embed.title == "Database Servers"