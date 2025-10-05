"""
Tests for WordleParser cog - Using conftest fixtures.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
import discord
from discord.ext import commands
from cogs.wordle_parser import WordleParser

# Test constants - fake IDs for predictable testing
FAKE_WORDLE_BOT_ID = 999999
FAKE_USER_ID = 123456789


@pytest.fixture
def parser_cog(mock_bot):
    """Create a WordleParser for testing using the mock_bot fixture."""
    return WordleParser(mock_bot)

@pytest.fixture  
def mock_message(mock_guild, mock_channel):
    """Create a mock Discord message for testing."""
    message = MagicMock(spec=discord.Message)
    message.author = MagicMock(spec=discord.Member)
    message.author.id = FAKE_WORDLE_BOT_ID  # Use constant for clarity
    message.guild = mock_guild
    message.channel = mock_channel
    message.content = ""
    return message

@pytest.mark.asyncio
async def test_ignores_own_messages(parser_cog, mock_message):
    """Test that bot ignores its own messages."""
    # Arrange - make the message from the bot itself
    parser_cog.bot.user = MagicMock()
    mock_message.author = parser_cog.bot.user
    mock_message.content = "day streak"
        
    # Act
    await parser_cog.on_message(mock_message)
        
    # Assert - should not try to parse anything
    mock_message.channel.send.assert_not_awaited()

@pytest.mark.asyncio  
async def test_detects_wordle_report(parser_cog, mock_message, sample_wordle_results):
    """Test that it detects a proper Wordle report message."""
    # Arrange
    parser_cog.wordle_bot_id = FAKE_WORDLE_BOT_ID  
    mock_message.content = sample_wordle_results
        
    # Mock the parse method to see if it gets called
    parser_cog.parse_wordle_results = AsyncMock()
        
    # Act
    await parser_cog.on_message(mock_message)
        
    # Assert
    parser_cog.parse_wordle_results.assert_awaited_once_with(mock_message)

@pytest.mark.asyncio
async def test_ignores_non_wordle_messages(parser_cog, mock_message):
    """Test that it ignores regular messages."""
    # Arrange
    parser_cog.wordle_bot_id = FAKE_WORDLE_BOT_ID
    mock_message.content = "Just a regular message"
    parser_cog.parse_wordle_results = AsyncMock()
        
    # Act
    await parser_cog.on_message(mock_message)
        
    # Assert - parse should NOT be called
    parser_cog.parse_wordle_results.assert_not_awaited()

@pytest.mark.asyncio
async def test_parse_single_user_score(parser_cog, mock_message, sample_wordle_results, mock_user, mocker):
    """Test parsing a message with one user score."""
    # Arrange
    mock_message.content = sample_wordle_results
        
    # Mock guild.get_member to return a fake user
    mock_message.guild.get_member.return_value = mock_user
    
    # Mock the DatabaseCog
    mock_database_cog = mocker.MagicMock()
    mock_database_cog.has_duplicate_submission.return_value = False
    mock_database_cog.save_wordle_score.return_value = True
    parser_cog.bot.get_cog.return_value = mock_database_cog

    # Act
    await parser_cog.parse_wordle_results(mock_message)
        
    # Assert - should send success message
    mock_message.channel.send.assert_awaited_once_with(
        "I've recorded the results for 2 participants. Better not have cheated."
    )

@pytest.mark.asyncio
async def test_parse_no_scores_found(parser_cog, mock_message, sample_wordle_results):
    """Test parsing a message with no valid scores."""
    # Arrange - message with no /6: patterns
    mock_message.content = sample_wordle_results.replace("/6:", "no score here")
        
    # Act
    await parser_cog.parse_wordle_results(mock_message)
        
    # Assert - should send "no scores" message
    mock_message.channel.send.assert_awaited_once_with(
        "I found nothing worth recording. Either the report is broken, or you've all collectively failed me."
    )

@pytest.mark.asyncio 
async def test_parse_failed_wordle_x_score(parser_cog, mock_message, sample_wordle_results, mock_user, mocker):
    """Test parsing a failed Wordle (X/6) gives 8 points."""
    # Arrange
    mock_message.content = sample_wordle_results.replace("4/6:", "X/6:")
    mock_message.guild.get_member.return_value = mock_user
    
    # Mock the DatabaseCog
    mock_database_cog = mocker.MagicMock()
    mock_database_cog.has_duplicate_submission.return_value = False
    mock_database_cog.save_wordle_score.return_value = True
    parser_cog.bot.get_cog.return_value = mock_database_cog
        
    # Act  
    await parser_cog.parse_wordle_results(mock_message)
        
    # Assert - should still count as 2 participants (one X/6, one 5/6)
    mock_message.channel.send.assert_awaited_once_with(
        "I've recorded the results for 2 participants. Better not have cheated."
    )

@pytest.mark.asyncio
async def test_processes_simulation_mode(parser_cog, mock_message, sample_wordle_results):
    """Test that it processes messages in simulation mode (wrong bot ID but right content)."""
    # Arrange
    parser_cog.wordle_bot_id = FAKE_WORDLE_BOT_ID  # Expecting this ID
    mock_message.author.id = 888888  # But message comes from different ID
    mock_message.content = sample_wordle_results  # But has the right content
    parser_cog.parse_wordle_results = AsyncMock()
    
    # Act
    await parser_cog.on_message(mock_message)
    
    # Assert - SHOULD process because of simulation mode (elif condition)
    parser_cog.parse_wordle_results.assert_awaited_once_with(mock_message)

@pytest.mark.asyncio
async def test_truly_ignores_non_wordle_content(parser_cog, mock_message):
    """Test that it ignores messages without Wordle keywords."""
    # Arrange
    parser_cog.wordle_bot_id = FAKE_WORDLE_BOT_ID
    mock_message.author.id = 888888  # Wrong ID
    mock_message.content = "Just a regular chat message"  # AND wrong content
    parser_cog.parse_wordle_results = AsyncMock()
    
    # Act
    await parser_cog.on_message(mock_message)
    
    # Assert - should NOT process (no keywords, wrong ID)
    parser_cog.parse_wordle_results.assert_not_awaited()