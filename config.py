import os


from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env file")

# Default notification frequency in hours
DEFAULT_NOTIFICATION_FREQUENCY = 2

# Major tech companies stock symbols
DEFAULT_STOCKS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "AMZN",  # Amazon
    "GOOGL",  # Google (Alphabet)
    "TSLA",  # Tesla
    "META",  # Meta (Facebook)
    "NVDA",  # NVIDIA
    "INTC",  # Intel
]

# Callback function to be called when stocks are updated
_stock_update_callback = None


def update_default_stocks(new_stocks):
    """Update the default stocks list and notify subscribers.

    Args:
        new_stocks: List of new stock symbols to set as default
    """
    global DEFAULT_STOCKS, _stock_update_callback
    DEFAULT_STOCKS = [stock.upper() for stock in new_stocks]
    if _stock_update_callback:
        _stock_update_callback()


def set_stock_update_callback(callback):
    """Set the callback function to be called when stocks are updated.

    Args:
        callback: Function to be called when stocks are updated
    """
    global _stock_update_callback
    _stock_update_callback = callback


# Logging Configuration
LOG_DIRECTORY = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOG_DIRECTORY, "bot.log")

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIRECTORY, exist_ok=True)
