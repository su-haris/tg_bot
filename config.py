import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
FAQ_URL = os.getenv('FAQ_URL')

# Common responses
WELCOME_MESSAGE = """Welcome to our Support Bot! 👋
I'm here to help you with your questions and issues.

Use these commands to get started:
/start - See this welcome message
/faq - Access our Frequently Asked Questions
/ticket - Create a new support ticket

Or just send me a message and I'll try to help you directly."""

FAQ_MESSAGE = f"You can find answers to common questions at: {FAQ_URL}"

TICKET_CREATED_MESSAGE = "Your ticket #{} has been created. We'll get back to you soon!"

# Pre-defined responses for common messages
COMMON_RESPONSES = {
    "help": "I'm here to help! You can ask me a question or create a support ticket with /ticket.",
    "help me": "I'll do my best to help you. Could you describe your issue or use /ticket to create a support ticket?"
}

# Common greetings that should trigger the welcome message
COMMON_GREETINGS = ["hello", "hi", "hey", "greetings", "howdy"]

# Data file path
DATA_FILE = 'data.json'
