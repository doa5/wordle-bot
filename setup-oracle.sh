#!/bin/bash
# * Generated with assistance from Copilot AI, I dont know much about Oracle Cloud
# Oracle Cloud VM Setup Script for Wordle Bot
# Run this script after creating your VM

echo "Setting up Wordle Bot on Oracle Cloud VM..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv git -y

# Clone the repository
cd /home/ubuntu
git clone https://github.com/doa5/wordle-bot.git
cd wordle-bot

# Switch to deployment branch
git checkout deployment

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (you'll need to edit this with your actual tokens)
cat > .env << EOF
DISCORD_TOKEN=your_discord_bot_token_here
WORDLE_BOT_ID=your_wordle_bot_id_here
EOF

echo "IMPORTANT: Edit /home/ubuntu/wordle-bot/.env with your actual Discord tokens!"

# Set up systemd service
sudo cp wordle-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wordle-bot

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /home/ubuntu/wordle-bot/.env with your Discord tokens"
echo "2. Run: sudo systemctl start wordle-bot"
echo "3. Check status: sudo systemctl status wordle-bot"
echo "4. View logs: sudo journalctl -u wordle-bot -f"