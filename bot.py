import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import (
    LOG_FILE,
    LOG_FORMAT,
    TELEGRAM_BOT_TOKEN,
    update_default_stocks,
    set_stock_update_callback,
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


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check current price of a stock or all subscribed stocks."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a stock symbol or 'all'. Example: /check AAPL or /check all"
        )
        return

    symbol = context.args[0].upper()
    user_id = str(update.effective_user.id)

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
        hours = int(context.args[0])
        if hours < 1:
            await update.message.reply_text("Frequency must be at least 1 hour.")
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


def main() -> None:
    """Start the bot."""
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
    scheduler.add_job(send_stock_updates, "interval", hours=2, args=[application])

    # Start both the scheduler and the bot in the same event loop
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,  # Keep the event loop open for the scheduler
    )
    scheduler.start()

    try:
        import asyncio

        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
