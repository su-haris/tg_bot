#!/usr/bin/env python
import json
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Data storage functions
def load_data():
    try:
        with open(config.DATA_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"tickets": {}, "ticket_counter": 0}


def save_data(data):
    with open(config.DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)


# Command handlers
async def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message when /start command is received"""
    if update.effective_message:
        await update.effective_message.reply_text(config.WELCOME_MESSAGE)


async def faq(update: Update, context: CallbackContext) -> None:
    """Send FAQ message when /faq command is received"""
    if update.effective_message:
        await update.effective_message.reply_text(config.FAQ_MESSAGE)


async def create_ticket(update: Update, context: CallbackContext) -> None:
    """Create a new ticket when /ticket command is received"""
    if not update.effective_message or not update.effective_chat:
        return

    data = load_data()
    data["ticket_counter"] += 1
    ticket_id = data["ticket_counter"]

    # Get user info
    user = update.effective_user
    if not user:
        await update.effective_message.reply_text("Error: Could not identify user")
        return

    username = user.username if user.username else f"{user.first_name} {user.last_name or ''}"

    # Initialize new ticket
    data["tickets"][str(ticket_id)] = {
        "user_id": user.id,
        "username": username,
        "status": "open",
        "messages": [],
        "chat_id": update.effective_chat.id
    }

    # Save updated ticket data
    save_data(data)

    # Notify user
    await update.effective_message.reply_text(config.TICKET_CREATED_MESSAGE.format(ticket_id))

    # Notify admin group
    admin_notification = (
        f"🎫 New Ticket #{ticket_id} 🎫\n"
        f"From: {username}\n"
        f"\nReply to this message to respond to the ticket."
    )

    try:
        admin_msg = await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID,
            text=admin_notification
        )

        # Store admin message ID for reference
        data["tickets"][str(ticket_id)]["admin_msg_id"] = admin_msg.message_id
        save_data(data)
    except Exception as e:
        logger.error(f"Failed to send message to admin group: {e}")
        await update.effective_message.reply_text("Error: Could not notify administrators")


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle regular messages from users and admins"""
    if not update.effective_message or not update.effective_chat:
        return

    # Ignore messages from admin group
    if str(update.effective_chat.id) == str(config.ADMIN_CHAT_ID):
        await handle_admin_message(update, context)
        return

    message_text = update.effective_message.text.lower() if update.effective_message.text else ""

    # Check for common greetings first - send welcome message
    for greeting in config.COMMON_GREETINGS:
        if greeting in message_text:
            await update.effective_message.reply_text(config.WELCOME_MESSAGE)
            return

    # Check for other common phrases
    for key, response in config.COMMON_RESPONSES.items():
        if key in message_text:
            await update.effective_message.reply_text(response)
            return

    # Handle as a general message from user
    user_id = update.effective_chat.id
    data = load_data()

    # Try to find an open ticket for this user
    found_ticket = None
    ticket_id = None

    for tid, ticket in data["tickets"].items():
        if ticket["chat_id"] == user_id and ticket["status"] == "open":
            found_ticket = ticket
            ticket_id = tid
            break

    if found_ticket:
        # Append to existing ticket
        found_ticket["messages"].append({
            "from": "user",
            "text": update.effective_message.text or ""
        })
        save_data(data)

        # Forward to admin group
        forward_message = (
            f"💬 Message from user (Ticket #{ticket_id}):\n"
            f"{update.effective_message.text or ''}\n\n"
            f"Reply to the original ticket message to respond."
        )

        try:
            await context.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=forward_message,
                reply_to_message_id=found_ticket.get("admin_msg_id")
            )
        except Exception as e:
            logger.error(f"Failed to forward message to admin group: {e}")
    else:
        # Create new ticket for the user
        data["ticket_counter"] += 1
        new_ticket_id = data["ticket_counter"]

        user = update.effective_user
        if not user:
            await update.effective_message.reply_text("Error: Could not identify user")
            return

        username = user.username if user.username else f"{user.first_name} {user.last_name or ''}"

        data["tickets"][str(new_ticket_id)] = {
            "user_id": user.id,
            "username": username,
            "status": "open",
            "messages": [{
                "from": "user",
                "text": update.effective_message.text or ""
            }],
            "chat_id": update.effective_chat.id
        }

        # Notify user that a ticket was automatically created
        await update.effective_message.reply_text(
            f"I've created a support ticket #{new_ticket_id} with your message. Our team will get back to you soon!"
        )

        # Notify admin group
        admin_notification = (
            f"🎫 New Ticket #{new_ticket_id} 🎫\n"
            f"From: {username}\n"
            f"Message: {update.effective_message.text or ''}\n\n"
            f"Reply to this message to respond to the ticket."
        )

        try:
            admin_msg = await context.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=admin_notification
            )

            # Store admin message ID for reference
            data["tickets"][str(new_ticket_id)]["admin_msg_id"] = admin_msg.message_id
            save_data(data)
        except Exception as e:
            logger.error(f"Failed to notify admin group: {e}")


async def handle_admin_message(update: Update, context: CallbackContext) -> None:
    """Handle replies from admins in the admin group"""
    if not update.effective_message or not update.effective_message.reply_to_message:
        return

    # Get original admin message that was replied to
    original_msg_id = update.effective_message.reply_to_message.message_id

    # Find which ticket this is a reply to
    data = load_data()
    target_ticket = None
    ticket_id = None

    for tid, ticket in data["tickets"].items():
        if ticket.get("admin_msg_id") == original_msg_id:
            target_ticket = ticket
            ticket_id = tid
            break

    if target_ticket and target_ticket["status"] == "open":
        # Record the admin's response in the ticket
        admin_user = update.effective_user
        admin_name = "Admin"
        admin_id = 0

        if admin_user:
            admin_name = admin_user.username or admin_user.first_name or "Admin"
            admin_id = admin_user.id

        target_ticket["messages"].append({
            "from": "admin",
            "text": update.effective_message.text or "",
            "admin_id": admin_id,
            "admin_name": admin_name
        })

        # Save the updated ticket data
        save_data(data)

        # Forward the response to the user
        user_notification = f"💬 Support response for ticket #{ticket_id}:\n\n{update.effective_message.text or ''}"

        try:
            await context.bot.send_message(
                chat_id=target_ticket["chat_id"],
                text=user_notification
            )

            # Confirm to the admin that the message was sent
            await update.effective_message.reply_text(f"✅ Response sent to the user (Ticket #{ticket_id})")
        except Exception as e:
            logger.error(f"Failed to send response to user: {e}")
            await update.effective_message.reply_text(f"❌ Failed to send response: {e}")

    elif target_ticket and target_ticket["status"] == "closed":
        await update.effective_message.reply_text(f"⚠️ Cannot reply: Ticket #{ticket_id} is closed.")
    else:
        await update.effective_message.reply_text("❌ Could not find the associated ticket for this reply.")


async def close_ticket(update: Update, context: CallbackContext) -> None:
    """Close a ticket using /close command"""
    if not update.effective_message or not update.effective_chat:
        return

    # Only admin group can close tickets
    if str(update.effective_chat.id) != str(config.ADMIN_CHAT_ID):
        await update.effective_message.reply_text("❌ Only administrators can close tickets.")
        return

    # Check if a ticket ID was provided
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("❌ Please provide a valid ticket ID: /close <ticket_id>")
        return

    ticket_id = context.args[0]
    data = load_data()

    if ticket_id in data["tickets"]:
        ticket = data["tickets"][ticket_id]

        # Check if ticket is already closed
        if ticket["status"] == "closed":
            await update.effective_message.reply_text(f"⚠️ Ticket #{ticket_id} is already closed.")
            return

        # Close the ticket
        ticket["status"] = "closed"
        save_data(data)

        # Notify admin
        await update.effective_message.reply_text(f"✅ Ticket #{ticket_id} has been closed.")

        # Notify user
        try:
            await context.bot.send_message(
                chat_id=ticket["chat_id"],
                text=f"Your support ticket #{ticket_id} has been closed. If you have further questions, please open a new ticket using /ticket."
            )
        except Exception as e:
            logger.error(f"Failed to notify user about ticket closure: {e}")
            await update.effective_message.reply_text(f"⚠️ Failed to notify user: {e}")
    else:
        await update.effective_message.reply_text(f"❌ Ticket #{ticket_id} not found.")


def main() -> None:
    """Start the bot."""
    # Validate that required environment variables are set
    if not config.BOT_TOKEN:
        logger.error("Bot token is not set in environment variables")
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

    if not config.ADMIN_CHAT_ID:
        logger.error("Admin chat ID is not set in environment variables")
        raise ValueError("ADMIN_CHAT_ID environment variable is required")

    # Create the Application with job_queue=None to fix Python 3.13 weak reference issue
    application = Application.builder().token(config.BOT_TOKEN).job_queue(None).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("faq", faq))
    application.add_handler(CommandHandler("ticket", create_ticket))
    application.add_handler(CommandHandler("close", close_ticket))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling()


if __name__ == '__main__':
    main()
