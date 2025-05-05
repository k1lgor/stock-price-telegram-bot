import asyncio
import datetime
import json
import logging
import os
import time

from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cachetools import TTLCache
from requests import get  # Add this import at the top
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import (
    LOG_FILE,
    LOG_FORMAT,
    TELEGRAM_BOT_TOKEN,
    set_stock_update_callback,
    update_default_stocks,
)
from database import Database
from stock_service import StockService

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize database and scheduler
db = Database()
scheduler = AsyncIOScheduler()

# Rate limiting cache: user_id -> last_command_time
command_cache = TTLCache(maxsize=1000, ttl=60)  # 1 minute cooldown


def rate_limit_decorator(func):
    """Decorator to apply rate limiting to commands."""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        current_time = time.time()

        # Check if user has issued a command recently
        if user_id in command_cache:
            last_time = command_cache[user_id]
            if current_time - last_time < 3:  # 3 seconds between commands
                await update.message.reply_text(
                    "Please wait a moment before using another command."
                )
                return

        # Update cache and proceed
        command_cache[user_id] = current_time
        return await func(update, context)

    return wrapper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to the Stock Price Notification Bot!\n\n"
        "I'll help you monitor stock prices of major tech companies. Here are my commands:\n\n"
        "/subscribe SYMBOL - Subscribe to a stock (e.g., /subscribe AAPL)\n"
        "/unsubscribe SYMBOL - Unsubscribe from a stock\n"
        "/check SYMBOL - Check current stock price\n"
        "/list - List all your subscribed stocks\n"
        "/frequency HOURS - Set notification frequency\n"
        "/updatestocks SYMBOL1 SYMBOL2 ... - Update the default stock list\n"
        "/help - Show this help message\n\n"
        "You're currently subscribed to receive updates every 2 hours for major tech stocks."
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    await start(update, context)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to a stock symbol."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a stock symbol. Example: /subscribe AAPL"
        )
        return

    symbol = context.args[0].upper()
    user_id = str(update.effective_user.id)

    # Validate the stock symbol
    if not StockService.validate_stock_symbol(symbol):
        await update.message.reply_text(f"Invalid stock symbol: {symbol}")
        return

    if db.subscribe_stock(user_id, symbol):
        await update.message.reply_text(f"Successfully subscribed to {symbol}")
    else:
        await update.message.reply_text(f"You're already subscribed to {symbol}")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from a stock symbol."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a stock symbol. Example: /unsubscribe AAPL"
        )
        return

    symbol = context.args[0].upper()
    user_id = str(update.effective_user.id)

    if db.unsubscribe_stock(user_id, symbol):
        await update.message.reply_text(f"Successfully unsubscribed from {symbol}")
    else:
        await update.message.reply_text(f"You're not subscribed to {symbol}")


@rate_limit_decorator
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check current price of a stock or all subscribed stocks."""
    user_id = str(update.effective_user.id)
    if not context.args:
        # No arguments: show all subscribed stocks
        stocks = db.get_subscribed_stocks(user_id)
        if not stocks:
            await update.message.reply_text("You're not subscribed to any stocks.")
            return

        stocks_info = StockService.get_multiple_stocks_info(stocks)
        if not stocks_info:
            await update.message.reply_text("Could not fetch data for your stocks.")
            return

        message = "📊 Current Stock Prices\n\n"
        for symbol, info in stocks_info.items():
            message += StockService.format_stock_message(info) + "\n"

        await update.message.reply_text(message)
        return

    symbol = context.args[0].upper()

    if symbol == "ALL":
        stocks = db.get_subscribed_stocks(user_id)
        if not stocks:
            await update.message.reply_text("You're not subscribed to any stocks.")
            return

        stocks_info = StockService.get_multiple_stocks_info(stocks)
        if not stocks_info:
            await update.message.reply_text("Could not fetch data for your stocks.")
            return

        message = "📊 Current Stock Prices\n\n"
        for symbol, info in stocks_info.items():
            message += StockService.format_stock_message(info) + "\n"

        await update.message.reply_text(message)
    else:
        stock_info = StockService.get_stock_info(symbol)
        if stock_info:
            message = StockService.format_stock_message(stock_info)
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(f"Could not fetch data for {symbol}")


async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all subscribed stocks."""
    user_id = str(update.effective_user.id)
    stocks = db.get_subscribed_stocks(user_id)

    if not stocks:
        await update.message.reply_text("You're not subscribed to any stocks.")
        return

    message = "Your subscribed stocks:\n\n"
    for symbol in stocks:
        message += f"• {symbol}\n"

    await update.message.reply_text(message)


async def set_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set notification frequency in hours."""
    if not context.args:
        await update.message.reply_text(
            "Please provide frequency in hours. Example: /frequency 2"
        )
        return

    try:
        hours = float(context.args[0])

        # More comprehensive validation
        if not hours.is_integer():
            await update.message.reply_text("Frequency must be an integer.")
            return

        hours = int(hours)
        if hours < 1 or hours > 24:
            await update.message.reply_text("Frequency must be between 1 and 24 hours.")
            return

        user_id = str(update.effective_user.id)
        db.set_notification_frequency(user_id, hours)
        await update.message.reply_text(f"Notification frequency set to {hours} hours.")

    except ValueError:
        await update.message.reply_text("Please provide a valid number of hours.")


async def update_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update the default stocks list."""
    if not context.args:
        await update.message.reply_text(
            "Please provide at least one stock symbol. Example: /updatestocks AAPL MSFT GOOGL"
        )
        return

    # Check if user is admin (you might want to add proper admin check)
    user_id = str(update.effective_user.id)

    # Convert all symbols to uppercase
    new_stocks = [symbol.upper() for symbol in context.args]

    # Validate all stock symbols
    invalid_symbols = []
    for symbol in new_stocks:
        if not StockService.validate_stock_symbol(symbol):
            invalid_symbols.append(symbol)

    if invalid_symbols:
        await update.message.reply_text(
            f"The following symbols are invalid: {', '.join(invalid_symbols)}\n"
            f"Please provide valid stock symbols."
        )
        return

    # Update the default stocks list
    update_default_stocks(new_stocks)

    await update.message.reply_text(
        f"Default stocks list updated successfully.\n"
        f"New default stocks: {', '.join(new_stocks)}"
    )


async def send_stock_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send stock updates to all users based on their preferences."""
    for user_id in db.get_all_users():
        stocks = db.get_subscribed_stocks(user_id)
        if not stocks:
            continue

        stocks_info = StockService.get_multiple_stocks_info(stocks)
        if not stocks_info:
            continue

        message = "📊 Stock Price Update\n\n"
        for symbol, info in stocks_info.items():
            message += StockService.format_stock_message(info) + "\n"

        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.error(f"Error sending update to user {user_id}: {e}")


async def health_check(request):
    """Enhanced health check endpoint."""
    try:
        # Verify database connection
        db.get_all_users()

        # Check YFinance API
        test_symbol = "AAPL"
        stock_info = StockService.get_stock_info(test_symbol)

        if stock_info:
            return web.Response(
                text=json.dumps(
                    {
                        "status": "healthy",
                        "database": "connected",
                        "api": "connected",
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                content_type="application/json",
                status=200,
            )
        else:
            return web.Response(
                text=json.dumps(
                    {
                        "status": "degraded",
                        "database": "connected",
                        "api": "error",
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
                content_type="application/json",
                status=200,
            )
    except Exception as e:
        return web.Response(
            text=json.dumps(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            content_type="application/json",
            status=500,
        )


async def start_web_server():
    """Start a simple web server for health checks."""
    app = web.Application()
    app.add_routes([web.get("/", health_check)])

    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Web server started on port {port}")
    return runner


async def main_async() -> None:
    """Async implementation of the bot's main function."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("list", list_stocks))
    application.add_handler(CommandHandler("frequency", set_frequency))
    application.add_handler(CommandHandler("updatestocks", update_stocks))

    # Set up stock update callback
    set_stock_update_callback(db.refresh_default_stocks)

    # Schedule periodic updates
    scheduler.add_job(
        send_stock_updates, "interval", minutes=120, args=[application]
    )  # <-- changed from 14 to 120

    # Schedule self-ping every 14 minutes (to keep Render.com alive)
    scheduler.add_job(self_ping, "interval", minutes=14)

    # Start the scheduler
    scheduler.start()

    # Set up webhook instead of polling to avoid conflicts
    webhook_url = os.environ.get("WEBHOOK_URL")
    port = int(os.environ.get("PORT", 8080))

    # Start the web server in the same event loop
    runner = await start_web_server()

    try:
        if webhook_url:
            # Use webhook mode when WEBHOOK_URL is provided
            await application.initialize()
            await application.start()
            await application.updater.start_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=TELEGRAM_BOT_TOKEN,
                webhook_url=f"{webhook_url}/{TELEGRAM_BOT_TOKEN}",
                allowed_updates=Update.ALL_TYPES,
            )
            logger.info(f"Bot started in webhook mode on port {port}")

            # Keep the application running
            while True:
                await asyncio.sleep(3600)  # Sleep for an hour
        else:
            # Fallback to polling mode for local development
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,  # Important: Drop pending updates to avoid conflicts
            )
            logger.info("Bot started in polling mode")

            # Keep the application running
            while True:
                await asyncio.sleep(3600)  # Sleep for an hour
    except (KeyboardInterrupt, SystemExit):
        # Shutdown gracefully
        scheduler.shutdown()
        await application.stop()
        await runner.cleanup()


SELF_PING_URL = os.environ.get(
    "SELF_PING_URL"
)  # Add this after your other config loads


def self_ping():
    """Ping the server itself to prevent idling (for Render.com)."""
    if SELF_PING_URL:
        try:
            get(SELF_PING_URL, timeout=10)
            logger.info("Self-ping successful.")
        except Exception as e:
            logger.warning(f"Self-ping failed: {e}")


def main() -> None:
    """Start the bot by running the async main function in an event loop."""
    try:
        # Create and run the event loop
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    main()
