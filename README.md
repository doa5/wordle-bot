# wordle-bot
Discord wordle bot for tracking Wordle scores

## Overview
This Discord bot automatically tracks Wordle scores posted in your server. It parses Wordle result messages, stores them in a SQLite database, and provides leaderboards to see who's the best Wordle player!

## Features
- 🎯 Automatically detects and records Wordle scores from messages
- 📊 Weekly and all-time leaderboards
- 📈 Personal statistics tracking
- 💾 SQLite database for persistent storage
- ✅ Visual feedback with reactions when scores are recorded

## Setup

### Prerequisites
- Python 3.8 or higher
- A Discord bot token ([Create one here](https://discord.com/developers/applications))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/doa5/wordle-bot.git
cd wordle-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
```bash
cp config.json.example config.json
```

4. Edit `config.json` and add your Discord bot token:
```json
{
  "token": "YOUR_DISCORD_BOT_TOKEN_HERE",
  "command_prefix": "!",
  "wordle_bot_id": null
}
```

5. Run the bot:
```bash
python bot.py
```

## Usage

### Automatic Score Recording
Simply paste your Wordle result in any channel where the bot has access:

```
Wordle 1,234 4/6

⬛⬛🟨⬛⬛
🟨🟩⬛⬛⬛
⬛🟩🟩🟩🟩
🟩🟩🟩🟩🟩
```

The bot will automatically:
- Parse the Wordle number and score
- Store it in the database
- React with ✅ to confirm recording

### Commands

- `!leaderboard` or `!lb` - Display the weekly leaderboard
- `!leaderboard all` - Display the all-time leaderboard
- `!stats` - Show your personal Wordle statistics
- `!help_wordle` - Display help information

## How It Works

1. **Message Monitoring**: The bot listens to all messages in channels it has access to
2. **Pattern Matching**: Uses regex to identify valid Wordle score messages
3. **Data Storage**: Stores user ID, username, Wordle number, score, and timestamp in SQLite
4. **Leaderboard Calculation**: Calculates average scores and ranks users
5. **Weekly Reset**: Leaderboards track weekly performance (Monday-Sunday)

## Database Schema

The bot uses a simple SQLite database with the following schema:

```sql
CREATE TABLE scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    wordle_number INTEGER NOT NULL,
    score INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    UNIQUE(user_id, wordle_number)
);
```

Scores are:
- 1-6: Number of guesses to solve
- 7: Failed attempt (X/6)

## Bot Permissions

The bot requires the following Discord permissions:
- Read Messages/View Channels
- Send Messages
- Add Reactions
- Embed Links

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
