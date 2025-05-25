# Telegram Support Bot

A simple Telegram bot that provides customer support functionality with a basic ticketing system.

## Features

- Welcome message (`/start`)
- Access to FAQ (`/faq`)
- Create support tickets (`/ticket`)
- Auto-create tickets from user messages
- Admin can respond to tickets via a group chat
- Close tickets (`/close <ticket_id>`)
- Pre-defined responses for common messages
- Store all data in a JSON file (no database required)

## Setup

1. **Create a Telegram Bot**
    - Talk to [BotFather](https://t.me/botfather) on Telegram
    - Use the `/newbot` command to create a new bot
    - Copy the API token provided by BotFather

2. **Create an Admin Group**
    - Create a new group in Telegram
    - Add your bot to the group
    - Make the bot an admin in the group
    - Get the chat ID of your group (use a bot like [@getidsbot](https://t.me/getidsbot))

3. **Configure the Environment**
    - Copy the `.env.example` file to `.env` (create it if one doesn't exist)
    - Add your Telegram bot token: `TELEGRAM_BOT_TOKEN=your_token_here`
    - Add your admin group chat ID: `ADMIN_CHAT_ID=your_group_chat_id_here`
    - Add your FAQ URL: `FAQ_URL=your_faq_url_here`

4. **Run with Docker** (Recommended)
   ```bash
   # Build and start the container
   docker-compose up -d

   # View logs
   docker-compose logs -f
   ```

5. **Run Locally** (Alternative)
   ```bash
   # Install dependencies
   pip install -r requirements.txt

   # Run the bot
   python bot.py
   ```

## How It Works

1. **User Side**
    - Users can start the bot with `/start`
    - They can access FAQ with `/faq`
    - They can create a ticket with `/ticket`
    - Any message sent to the bot will either:
        - Get a pre-defined response if it matches common patterns
        - Create a new ticket or add to an existing open ticket

2. **Admin Side**
    - All tickets appear in the admin group chat
    - Admins can reply to these messages to respond to the user
    - Admins can close tickets with `/close ticket_id`

## Data Storage

Ticket data is stored in `data.json`. The file is created automatically if it doesn't exist or is empty.
