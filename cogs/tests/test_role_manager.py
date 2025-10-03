"""
Tests for RoleCog - Using conftest fixtures.
"""
import pytest
import discord
from discord.ext import commands
from cogs.role_manager import RoleCog


@pytest.fixture
def role_cog(mock_bot):
    """Create a RoleCog instance for testing."""
    return RoleCog(mock_bot)


@pytest.fixture
def mock_ctx_with_author(mock_ctx, mock_user):
    """Create a mock context with a properly set up author."""
    mock_ctx.author = mock_user
    mock_ctx.author.mention = "@testuser" 
    return mock_ctx


@pytest.mark.asyncio
async def test_done_role_found_and_assigned(role_cog, mock_ctx_with_author, mocker):
    """Test successful role assignment when 'done' role exists."""
    # Arrange
    role = mocker.MagicMock(spec=discord.Role)
    role.name = "done"
    mock_ctx_with_author.guild.roles = [role]
    
    # Mock discord.utils.get to return our role
    mock_get = mocker.patch('discord.utils.get', return_value=role)
    log_info = mocker.patch("logging.info")
    
    # Act
    await role_cog.done.callback(role_cog, mock_ctx_with_author)
    
    # Assert
    mock_get.assert_called_once_with(mock_ctx_with_author.guild.roles, name="done")
    mock_ctx_with_author.author.add_roles.assert_awaited_once_with(role)
    mock_ctx_with_author.send.assert_awaited_once_with(
        "@testuser, so you're done? Well done on completing today's puzzle."
    )
    log_info.assert_called_once()


@pytest.mark.asyncio
async def test_done_role_not_found(role_cog, mock_ctx_with_author, mocker):
    """Test behavior when 'done' role doesn't exist."""
    # Arrange
    mock_ctx_with_author.guild.roles = []
    mock_ctx_with_author.guild.name = "TestGuild"
    
    # Mock discord.utils.get to return None (role not found)
    mock_get = mocker.patch('discord.utils.get', return_value=None)
    log_warn = mocker.patch("logging.warning")
    
    # Act
    await role_cog.done.callback(role_cog, mock_ctx_with_author)
    
    # Assert
    mock_get.assert_called_once_with(mock_ctx_with_author.guild.roles, name="done")
    mock_ctx_with_author.author.add_roles.assert_not_awaited()
    mock_ctx_with_author.send.assert_awaited_once_with(
        "I'm afraid I can't find the 'done' role. Perhaps it needs to be created first?"
    )
    log_warn.assert_called_once_with("Role 'done' not found in guild TestGuild")


@pytest.mark.asyncio
async def test_done_role_assignment_fails(role_cog, mock_ctx_with_author, mocker):
    """Test error handling when role assignment fails."""
    # Arrange
    role = mocker.MagicMock(spec=discord.Role)
    role.name = "done"
    mock_ctx_with_author.author.add_roles = mocker.AsyncMock(
        side_effect=discord.Forbidden(mocker.MagicMock(), "Insufficient permissions")
    )
    
    mocker.patch('discord.utils.get', return_value=role)
    
    # Act & Assert - Should propagate the exception
    with pytest.raises(discord.Forbidden):
        await role_cog.done.callback(role_cog, mock_ctx_with_author)


@pytest.mark.asyncio
async def test_remove_done_roles_success(role_cog, mocker):
    """Test successful removal of done roles from multiple members."""
    # Arrange
    guild = mocker.MagicMock(spec=discord.Guild)
    guild.name = "TestGuild"
    
    role = mocker.MagicMock(spec=discord.Role)
    role.name = "done"
    
    # Create members with and without the role
    member1 = mocker.MagicMock(spec=discord.Member)
    member1.name = "User1"
    member1.roles = [role]
    member1.remove_roles = mocker.AsyncMock()
    
    member2 = mocker.MagicMock(spec=discord.Member)
    member2.name = "User2"
    member2.roles = []
    
    member3 = mocker.MagicMock(spec=discord.Member)
    member3.name = "User3"
    member3.roles = [role]
    member3.remove_roles = mocker.AsyncMock()
    
    guild.members = [member1, member2, member3]
    
    mocker.patch('discord.utils.get', return_value=role)
    log_info = mocker.patch("logging.info")
    
    # Act
    result = await role_cog._remove_done_roles(guild)
    
    # Assert
    assert result == 2  # Only 2 members had the role removed
    member1.remove_roles.assert_awaited_once_with(role)
    member3.remove_roles.assert_awaited_once_with(role)
    assert log_info.call_count == 2  # Called for each removal


@pytest.mark.asyncio
async def test_remove_done_roles_with_notification(role_cog, mocker):
    """Test role removal with channel notification."""
    # Arrange
    guild = mocker.MagicMock(spec=discord.Guild)
    channel = mocker.MagicMock(spec=discord.TextChannel)
    channel.send = mocker.AsyncMock()
    
    role = mocker.MagicMock(spec=discord.Role)
    member = mocker.MagicMock(spec=discord.Member)
    member.name = "TestUser"
    member.roles = [role]
    member.remove_roles = mocker.AsyncMock()
    
    guild.members = [member]
    mocker.patch('discord.utils.get', return_value=role)
    
    # Act
    result = await role_cog._remove_done_roles(guild, channel)
    
    # Assert
    assert result == 1
    channel.send.assert_awaited_once_with(
        "Good morning, everyone. I've reset the roles for 1 members. Good luck with today's puzzle."
    )


@pytest.mark.asyncio
async def test_remove_done_roles_no_role_found(role_cog, mocker):
    """Test behavior when 'done' role doesn't exist."""
    # Arrange
    guild = mocker.MagicMock(spec=discord.Guild)
    guild.name = "TestGuild"
    
    mocker.patch('discord.utils.get', return_value=None)
    log_warn = mocker.patch("logging.warning")
    
    # Act
    result = await role_cog._remove_done_roles(guild)
    
    # Assert
    assert result == 0
    log_warn.assert_called_once_with("Role 'done' not found in TestGuild")