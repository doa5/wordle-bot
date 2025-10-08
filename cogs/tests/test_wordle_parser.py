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
    message.id = 123456789  # Add message ID for processing_manual check
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
    
    # Mock get_context to return a non-valid context (not a bot command)
    mock_ctx = MagicMock()
    mock_ctx.valid = False
    parser_cog.bot.get_context = AsyncMock(return_value=mock_ctx)
        
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
    
    # Mock get_context to return a non-valid context (not a bot command)
    mock_ctx = MagicMock()
    mock_ctx.valid = False
    parser_cog.bot.get_context = AsyncMock(return_value=mock_ctx)
    
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


@pytest.mark.asyncio
@pytest.mark.parametrize("date_str,expected", [
    ("2024-06-01", True),
    ("2024-13-01", False),  # Invalid month
    ("2024-06-32", False),  # Invalid day
    ("2024/06/01", False),  # Wrong separator
    ("06-01-2024", False),  # Wrong format
    ("", False),            # Empty string
])
async def test_validate_date(parser_cog, date_str, expected, mocker):
        ctx = MagicMock()
        ctx.message.add_reaction = AsyncMock()
        ctx.send = AsyncMock()
        result = await parser_cog.validate_date(date_str, ctx)
        assert result is expected
        if not expected:
            ctx.message.add_reaction.assert_awaited_with("❌")
            ctx.send.assert_awaited_with("Your date format is... inadequate. Use YYYY-MM-DD format. Precision matters. Zero-pad single digits.")


@pytest.mark.asyncio
async def test_add_manual_score_valid_single_user(parser_cog, mocker):
        ctx = MagicMock()
        ctx.author.id = 1111
        ctx.guild.id = 2222
        ctx.guild.get_member.return_value = MagicMock(display_name="TestUser")
        ctx.message.add_reaction = AsyncMock()
        ctx.send = AsyncMock()
        parser_cog.validate_date = AsyncMock(return_value=True)
        db_cog = mocker.MagicMock()
        db_cog.has_duplicate_submission.return_value = False
        db_cog.save_wordle_score.return_value = True
        parser_cog.bot.get_cog.return_value = db_cog

        await parser_cog.add_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data="3/6")
        ctx.message.add_reaction.assert_awaited_with("✅")
        ctx.send.assert_awaited_with(
            "Score has been properly documented.\nDate: 2024-06-01\nEntries processed: 1\nMaintaining accurate records is essential."
        )


@pytest.mark.asyncio
async def test_add_manual_score_duplicate_submission(parser_cog, mocker):
    ctx = MagicMock()
    ctx.author.id = 1111
    ctx.guild.id = 2222
    ctx.guild.get_member.return_value = MagicMock(display_name="TestUser")
    ctx.message.add_reaction = AsyncMock()
    ctx.send = AsyncMock()
    parser_cog.validate_date = AsyncMock(return_value=True)
    db_cog = mocker.MagicMock()
    db_cog.has_duplicate_submission.return_value = True
    db_cog.save_wordle_score.return_value = True
    parser_cog.bot.get_cog.return_value = db_cog

    await parser_cog.add_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data="3/6")
    ctx.send.assert_awaited()
    # Check that success reaction was not added (should only add error reactions for duplicates)
    ctx.message.add_reaction.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_manual_score_invalid_score_format(parser_cog, mocker):
        ctx = MagicMock()
        ctx.author.id = 1111
        ctx.guild.id = 2222
        ctx.message.add_reaction = AsyncMock()
        ctx.send = AsyncMock()
        parser_cog.validate_date = AsyncMock(return_value=True)
        parser_cog.bot.get_cog.return_value = mocker.MagicMock()

        await parser_cog.add_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data="badscore")
        ctx.message.add_reaction.assert_awaited_with("❌")
        ctx.send.assert_awaited_with(
            "No valid score format found. Use formats like: 3/6, X/6, 3/6: @user, or just 3"
        )


@pytest.mark.asyncio
async def test_add_manual_score_invalid_score_value(parser_cog, mocker):
    ctx = MagicMock()
    ctx.author.id = 1111
    ctx.guild.id = 2222
    ctx.guild.get_member.return_value = MagicMock(display_name="TestUser")
    ctx.message.add_reaction = AsyncMock()
    ctx.send = AsyncMock()
    parser_cog.validate_date = AsyncMock(return_value=True)
    parser_cog.bot.get_cog.return_value = mocker.MagicMock()

    await parser_cog.add_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data="9/6")
    ctx.send.assert_awaited_with("❌ Invalid score 9/6 - must be 1-6 or X")


@pytest.mark.asyncio
async def test_add_manual_score_multiple_users_wordle_format(parser_cog, mocker):
    ctx = MagicMock()
    ctx.guild.id = 2222
    ctx.guild.get_member.return_value = MagicMock(display_name="UserA")
    ctx.author.id = 1111
    ctx.message.add_reaction = AsyncMock()
    ctx.send = AsyncMock()
    parser_cog.validate_date = AsyncMock(return_value=True)
    db_cog = mocker.MagicMock()
    db_cog.has_duplicate_submission.return_value = False
    db_cog.save_wordle_score.return_value = True
    parser_cog.bot.get_cog.return_value = db_cog

    score_data = "3/6: <@1111> 4/6: <@2222>"
    await parser_cog.add_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data=score_data)
    ctx.message.add_reaction.assert_awaited_with("✅")
    ctx.send.assert_awaited_with(
        "Multiple scores have been recorded.\nDate: 2024-06-01\nEntries processed: 2\nEfficiency noted."
    )


@pytest.mark.asyncio
async def test_add_manual_score_database_unavailable(parser_cog, mocker):
    ctx = MagicMock()
    ctx.author.id = 1111
    ctx.guild.id = 2222
    ctx.message.add_reaction = AsyncMock()
    ctx.send = AsyncMock()
    parser_cog.validate_date = AsyncMock(return_value=True)
    parser_cog.bot.get_cog.return_value = None

    await parser_cog.add_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data="3/6")
    ctx.message.add_reaction.assert_awaited_with("❌")
    ctx.send.assert_awaited_with(
        "The database is currently unavailable. Even champions need proper record-keeping systems."
    )


@pytest.mark.asyncio
async def test_overwrite_manual_score_valid(parser_cog, mocker):
    ctx = MagicMock()
    ctx.author.id = 1111
    ctx.guild.id = 2222
    ctx.guild.get_member.return_value = MagicMock(display_name="TestUser")
    ctx.message.add_reaction = AsyncMock()
    ctx.send = AsyncMock()
    parser_cog.validate_date = AsyncMock(return_value=True)
    db_cog = mocker.MagicMock()
    db_cog.save_wordle_score.return_value = True
    parser_cog.bot.get_cog.return_value = db_cog

    await parser_cog.overwrite_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data="3/6")
    ctx.message.add_reaction.assert_awaited_with("✅")
    ctx.send.assert_awaited_with(
        "Previous record has been corrected and updated.\nDate: 2024-06-01\nEntries modified: 1\nAccuracy is paramount."
    )


@pytest.mark.asyncio
async def test_overwrite_manual_score_multiple_users(parser_cog, mocker):
    ctx = MagicMock()
    ctx.guild.id = 2222
    ctx.guild.get_member.return_value = MagicMock(display_name="UserA")
    ctx.author.id = 1111
    ctx.message.add_reaction = AsyncMock()
    ctx.send = AsyncMock()
    parser_cog.validate_date = AsyncMock(return_value=True)
    db_cog = mocker.MagicMock()
    db_cog.save_wordle_score.return_value = True
    parser_cog.bot.get_cog.return_value = db_cog

    score_data = "3/6: <@1111> 4/6: <@2222>"
    await parser_cog.overwrite_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data=score_data)
    ctx.message.add_reaction.assert_awaited_with("✅")
    ctx.send.assert_awaited_with(
        "Multiple records have been corrected.\nDate: 2024-06-01\nEntries modified: 2\nPrecision maintained."
    )


@pytest.mark.asyncio
async def test_overwrite_manual_score_invalid_format(parser_cog, mocker):
    ctx = MagicMock()
    ctx.author.id = 1111
    ctx.guild.id = 2222
    ctx.message.add_reaction = AsyncMock()
    ctx.send = AsyncMock()
    parser_cog.validate_date = AsyncMock(return_value=True)
    parser_cog.bot.get_cog.return_value = mocker.MagicMock()

    await parser_cog.overwrite_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data="badscore")
    ctx.message.add_reaction.assert_awaited_with("❌")
    ctx.send.assert_awaited_with(
        "No valid score format found. Use formats like: 3/6, X/6, 3/6: @user, or just 3"
    )


@pytest.mark.asyncio
async def test_overwrite_manual_score_database_unavailable(parser_cog, mocker):
    ctx = MagicMock()
    ctx.author.id = 1111
    ctx.guild.id = 2222
    ctx.message.add_reaction = AsyncMock()
    ctx.send = AsyncMock()
    parser_cog.validate_date = AsyncMock(return_value=True)
    parser_cog.bot.get_cog.return_value = None

    await parser_cog.overwrite_manual_score.callback(parser_cog, ctx, "2024-06-01", score_data="3/6")
    ctx.message.add_reaction.assert_awaited_with("❌")
    ctx.send.assert_awaited_with(
        "Database systems are offline. Even the best strategies require functional infrastructure."
    )
