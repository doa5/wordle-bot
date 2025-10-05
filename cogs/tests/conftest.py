"""
Conftest.py - Shared fixtures and configuration for pytest.

This file contains reusable fixtures that can be used across all test files
to reduce code duplication and provide consistent test setup.

NOTE: pytest automatically finds fixtures in conftest.py files!
"""
import pytest
import discord
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot for testing."""
    bot = MagicMock(spec=commands.Bot)
    bot.guilds = []
    return bot


@pytest.fixture
def mock_guild():
    """Create a mock Discord guild/server."""
    guild = MagicMock(spec=discord.Guild)
    guild.name = "Test Server"
    guild.id = 12345
    guild.roles = []
    guild.members = []
    guild.channels = []
    return guild


@pytest.fixture
def mock_user():
    """Create a mock Discord user."""
    user = MagicMock(spec=discord.Member)
    user.name = "TestUser"
    user.id = 67890
    user.mention = "@TestUser"
    user.roles = []
    user.add_roles = AsyncMock()
    user.remove_roles = AsyncMock()
    return user


@pytest.fixture
def mock_role():
    """Create a mock Discord role."""
    role = MagicMock(spec=discord.Role)
    role.name = "done"
    role.id = 11111
    return role


@pytest.fixture
def mock_channel():
    """Create a mock Discord text channel."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "general"
    channel.id = 22222
    channel.send = AsyncMock()
    return channel


@pytest.fixture
def mock_ctx(mock_guild, mock_user, mock_channel):
    """Create a comprehensive mock context."""
    ctx = MagicMock(spec=commands.Context)
    ctx.guild = mock_guild
    ctx.author = mock_user
    ctx.channel = mock_channel
    ctx.send = AsyncMock()
    return ctx


# Test data fixtures
@pytest.fixture
def sample_wordle_results():
    """Sample Wordle results for testing parsing."""
    return """Your group is on an 87 day streak!  Here are yesterday's results: 
4/6:  <@383926733394542592>  
5/6:   <@714203809529856110>"""


@pytest.fixture
def sample_database_scores():
    """Sample database score data for testing."""
    return [
        {"user_id": 67890, "username": "TestUser", "puzzle_number": 1234, "score": 3, "date": "2024-01-15"},
        {"user_id": 67891, "username": "TestUser2", "puzzle_number": 1234, "score": 4, "date": "2024-01-15"},
        {"user_id": 67892, "username": "TestUser3", "puzzle_number": 1234, "score": 8, "date": "2024-01-15"}  # X/6 = 8
    ]