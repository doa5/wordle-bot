import pytest
import random
from unittest import mock
from cogs.oguri_cap import OguriCapCog

@pytest.fixture
def bot():
    return mock.Mock()

@pytest.fixture
def cog(bot):
    return OguriCapCog(bot)

def test_get_random_gif_valid_category(cog):
    category = 'eating'
    gifs = cog.gifs[category]
    # Patch random.choice to always return the first gif
    with mock.patch('random.choice', return_value=gifs[0]):
        result = cog.get_random_gif(category)
        assert result == gifs[0]

def test_get_random_gif_invalid_category(cog):
    assert cog.get_random_gif('unknown') is None

def test_get_random_gif_empty_category(cog):
    cog.gifs['empty'] = []
    assert cog.get_random_gif('empty') is None

@pytest.mark.asyncio
async def test_on_message_triggers_response(cog, bot):
    message = mock.Mock()
    message.author = mock.Mock()
    bot.user = mock.Mock()
    message.content = "I love food"
    message.channel = mock.AsyncMock()
    
    message.author = "not_the_bot"
    bot.user = "the_bot"
    
    await cog.on_message(message)
    message.channel.send.assert_called_once()

@pytest.mark.asyncio
async def test_on_message_ignores_bot(cog, bot):
    message = mock.Mock()
    message.author = bot.user
    message.content = "food"
    message.channel = mock.AsyncMock()
    await cog.on_message(message)
    message.channel.send.assert_not_called()

@pytest.mark.asyncio
async def test_snack_command_sends_embed(cog):
    ctx = mock.AsyncMock()
    # Patch random.choice for gif and satisfaction
    with mock.patch('random.choice', side_effect=[
        cog.gifs['eating'][0],  # gif_url
        "Eating well is part of the race too."  # satisfaction
    ]):
        with mock.patch('asyncio.sleep', return_value=None):
            await cog.snack.callback(cog, ctx)

    ctx.send.assert_called_once()
    call_args = ctx.send.call_args
    embed = call_args[1]['embed'] if call_args[1] else call_args[0][0]
    
    assert embed.title == "Snack time"
    assert embed.description in [
        "Eating well is part of the race too.",
        "I can't go all-out on an empty stomach.",
        "I run. I earned this."
    ]

@pytest.mark.asyncio
async def test_celebrate_victory_command_sends_embed(cog):
    ctx = mock.AsyncMock()
    with mock.patch('random.choice', return_value=cog.gifs['victory'][0]):
        await cog.celebrate_victory.callback(cog, ctx)
    # Check that ctx.send was called with an embed
    ctx.send.assert_called_once()
    call_args = ctx.send.call_args
    embed = call_args[1]['embed'] if call_args[1] else call_args[0][0]
    
    assert embed.title == "A fine victory for Mr. Tricks"
    assert embed.description == "AND THE GOAT WINS AGAIN 🎉"