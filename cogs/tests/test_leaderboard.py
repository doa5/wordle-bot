import pytest
from unittest import mock
from datetime import datetime
from cogs.leaderboard import LeaderboardCog

@pytest.fixture
def mock_bot():
    """Create a mock Discord bot for testing. """
    return mock.Mock()

@pytest.fixture
def cog(mock_bot):
    """Create an instance of LeaderboardCog with a mock bot. """
    return LeaderboardCog(mock_bot)

def test_is_leaderboard_available_sunday_5pm(monkeypatch, cog):
    """Test that leaderboard is available on Sunday at 5 PM. """
    # Sunday at 17:00:00
    dt = datetime(2024, 6, 9, 17, 0, 0)
    monkeypatch.setattr('cogs.leaderboard.datetime', mock.Mock(now=mock.Mock(return_value=dt), time=dt.time))
    assert cog.is_leaderboard_available() is True

def test_is_leaderboard_available_sunday_before_5pm(monkeypatch, cog):
    """Test that leaderboard is not available before Sunday at 5 PM. """
    # Sunday at 16:59:59
    dt = datetime(2024, 6, 9, 16, 59, 59)
    monkeypatch.setattr('cogs.leaderboard.datetime', mock.Mock(now=mock.Mock(return_value=dt), time=dt.time))
    assert cog.is_leaderboard_available() is False

def test_is_leaderboard_available_sunday_after_midnight(monkeypatch, cog):
    """Test that leaderboard is not available after Sunday at midnight. """
    # Monday at 00:00:00
    dt = datetime(2024, 6, 10, 0, 0, 0)
    monkeypatch.setattr('cogs.leaderboard.datetime', mock.Mock(now=mock.Mock(return_value=dt), time=dt.time))
    assert cog.is_leaderboard_available() is False

def test_is_leaderboard_available_not_sunday(monkeypatch, cog):
    """Test that leaderboard is not available on days other than Sunday. """
    # Wednesday at 18:00:00
    dt = datetime(2024, 6, 12, 18, 0, 0)
    monkeypatch.setattr('cogs.leaderboard.datetime', mock.Mock(now=mock.Mock(return_value=dt), time=dt.time))
    assert cog.is_leaderboard_available() is False

def test_get_next_sunday_5pm_on_monday(monkeypatch, cog):
    """Test getting next Sunday 5 PM from a Monday."""
    dt = datetime(2024, 6, 10, 10, 0, 0)  # Monday
    monkeypatch.setattr('cogs.leaderboard.datetime', mock.Mock(now=mock.Mock(return_value=dt), time=dt.time))
    result = cog._get_next_sunday_5pm()
    assert result.weekday() == 6
    assert result.hour == 17 and result.minute == 0

def test_get_next_sunday_5pm_on_sunday_before_5pm(monkeypatch, cog):
    """Test getting next Sunday 5 PM from a Sunday before 5 PM."""
    dt = datetime(2024, 6, 9, 10, 0, 0)  # Sunday before 5pm
    monkeypatch.setattr('cogs.leaderboard.datetime', mock.Mock(now=mock.Mock(return_value=dt), time=dt.time))
    result = cog._get_next_sunday_5pm()
    assert result.date() == dt.date()
    assert result.hour == 17 and result.minute == 0

@pytest.mark.asyncio
async def test_leaderboard_not_available(cog):
    """Test leaderboard command when leaderboard is not available."""
    # Patch is_leaderboard_available to False
    cog.is_leaderboard_available = mock.Mock(return_value=False)
    cog._get_next_sunday_5pm = mock.Mock(return_value=datetime(2024, 6, 16, 17, 0, 0))
    ctx = mock.AsyncMock()
    await cog.leaderboard.callback(cog, ctx)
    ctx.send.assert_called_once()
    assert "Next available" in ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_leaderboard_available(cog):
    """Test leaderboard command when leaderboard is available."""
    cog.is_leaderboard_available = mock.Mock(return_value=True)
    cog.produce_leaderboard = mock.AsyncMock()
    ctx = mock.AsyncMock()
    await cog.leaderboard.callback(cog, ctx)
    cog.produce_leaderboard.assert_awaited_once_with(ctx)

@pytest.mark.asyncio
async def test_produce_leaderboard_no_database(cog):
    """Test produce_leaderboard when database cog is not available."""
    cog.bot.get_cog = mock.Mock(return_value=None)
    ctx = mock.AsyncMock()
    await cog.produce_leaderboard(ctx)
    ctx.send.assert_called_once_with("Database unavailable.")

@pytest.mark.asyncio
async def test_produce_leaderboard_no_results(cog):
    """Test produce_leaderboard when no results are found."""
    database_cog = mock.Mock()
    database_cog.execute_query.return_value = []
    cog.bot.get_cog = mock.Mock(return_value=database_cog)
    ctx = mock.AsyncMock()
    ctx.guild.id = 123
    await cog.produce_leaderboard(ctx)
    ctx.send.assert_called_once_with("No scores recorded this week.")

@pytest.mark.asyncio
async def test_produce_leaderboard_with_results(cog):
    """Test produce_leaderboard when results are found."""
    database_cog = mock.Mock()
    database_cog.execute_query.return_value = [
        ("Oguri Cap", 5, 3),
        ("Symboli Rudolf", 7, 3),
        ("TM Opera O", 8, 2),
        ("Manhattan Cafe", 10, 4),
    ]
    cog.bot.get_cog = mock.Mock(return_value=database_cog)
    ctx = mock.AsyncMock()
    ctx.guild.id = 123
    await cog.produce_leaderboard(ctx)
    ctx.send.assert_called_once()
    msg = ctx.send.call_args[0][0]
    assert "Weekly Wordle Leaderboard" in msg
    assert "👑 **Oguri Cap**" in msg
    assert "🥈 **Symboli Rudolf**" in msg
    assert "🥉 **TM Opera O**" in msg
    assert "4. **Manhattan Cafe**" in msg

@pytest.mark.asyncio
async def test_leaderboard_status(cog):
    """Test leaderboard_status command."""
    cog.is_leaderboard_available = mock.Mock(return_value=True)
    cog._get_next_sunday_5pm = mock.Mock(return_value=datetime(2024, 6, 16, 17, 0, 0))
    ctx = mock.AsyncMock()
    await cog.leaderboard_status.callback(cog, ctx)
    ctx.send.assert_called_once()
    msg = ctx.send.call_args[0][0]
    assert "Status report:" in msg
    assert "Leaderboard access: True" in msg

@pytest.mark.asyncio
async def test_reset_leaderboard_no_database(cog):
    """Test reset_leaderboard when database cog is not available."""
    cog.bot.get_cog = mock.Mock(return_value=None)
    ctx = mock.AsyncMock()
    await cog.reset_leaderboard.callback(cog, ctx)
    ctx.send.assert_called_once_with("Database unavailable.")

@pytest.mark.asyncio
async def test_reset_leaderboard_with_results(cog):
    """Test reset_leaderboard when there are entries to clear."""
    database_cog = mock.Mock()
    database_cog.execute_query.return_value = [1, 2, 3]
    cog.bot.get_cog = mock.Mock(return_value=database_cog)
    ctx = mock.AsyncMock()
    ctx.guild.id = 123
    await cog.reset_leaderboard.callback(cog, ctx)
    ctx.send.assert_called_once()
    msg = ctx.send.call_args[0][0]
    assert "Archives cleared. 3 entries processed." in msg

@pytest.mark.asyncio
async def test_show_leaderboard(cog):
    """Test show_leaderboard command."""
    cog.produce_leaderboard = mock.AsyncMock()
    ctx = mock.AsyncMock()
    await cog.show_leaderboard.callback(cog, ctx)
    cog.produce_leaderboard.assert_awaited_once_with(ctx)