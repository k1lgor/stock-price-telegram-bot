# Stock Price Notification Telegram Bot

A Telegram bot that monitors stock prices of major tech companies and sends periodic updates to users.

## Features

- Monitor stock prices of major tech companies (Apple, Microsoft, Amazon, Google, Tesla)
- Periodic notifications (every 2 hours by default; server self-pings every 14 minutes to stay awake on Render.com)
- Subscribe/unsubscribe to specific stocks
- Manual stock price checking
- Customizable notification frequency
- Real-time stock data from Yahoo Finance

## Commands

- `/start` - Start the bot and get welcome message
- `/subscribe SYMBOL` - Subscribe to a specific stock (e.g., `/subscribe AAPL`)
- `/unsubscribe SYMBOL` - Unsubscribe from a specific stock
- `/check SYMBOL` - Check current stock price
- `/check all` - Check prices of all subscribed stocks
- `/list` - List all subscribed stocks
- `/frequency HOURS` - Set notification frequency in hours (e.g., `/frequency 1`)
- `/updatestocks SYMBOL1 SYMBOL2 ...` - Update the default list of monitored stocks
- `/help` - Show available commands

## Setup Instructions

1. Clone the repository
2. Install Poetry (if not already installed):

   ```bash
   pip install poetry
   ```

3. Install dependencies:

   ```bash
   poetry install
   ```

4. Create a `.env` file with your Telegram Bot Token:

   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   SELF_PING_URL=https://your-app-name.onrender.com/
   ```

5. Run the bot:

   ```bash
   poetry run python bot.py
   ```

## Using the Telegram Bot (@BigTechStocks_bot)

1. **Find the Bot**:
   - Open Telegram and search for `@BigTechStocks_bot` in the search bar
   - Or click on this link: [t.me/BigTechStocks_bot](https://t.me/BigTechStocks_bot)

2. **Start the Bot**:
   - Click on the "Start" button or send the `/start` command
   - The bot will send a welcome message with basic instructions

3. **Subscribe to Stocks**:
   - By default, you're subscribed to major tech stocks (AAPL, MSFT, AMZN, GOOGL, TSLA)
   - To add more stocks: `/subscribe SYMBOL` (e.g., `/subscribe NVDA`)
   - To remove stocks: `/unsubscribe SYMBOL` (e.g., `/unsubscribe TSLA`)

4. **Check Stock Prices**:
   - Check a specific stock: `/check SYMBOL` (e.g., `/check AAPL`)
   - Check all your subscribed stocks: `/check all`

5. **Manage Notifications**:
   - List your subscribed stocks: `/list`
   - Change notification frequency: `/frequency HOURS` (e.g., `/frequency 1` for hourly updates)
   - Update your entire stock list at once: `/updatestocks AAPL MSFT META` (replaces your current list)

6. **Get Help**:
   - Send `/help` anytime to see all available commands

## Project Structure

- `bot.py` - Main bot implementation
- `stock_service.py` - Stock data fetching and processing
- `database.py` - User preferences and subscription management
- `config.py` - Configuration and environment variables
- `utils.py` - Utility functions

## Dependencies

- python-telegram-bot - Telegram Bot API wrapper
- yfinance - Yahoo Finance API wrapper
- APScheduler - Task scheduling
- python-dotenv - Environment variable management
- requests - HTTP requests

## Error Handling

The bot includes comprehensive error handling for:

- API failures
- Network connectivity issues
- Invalid user inputs
- Rate limiting

## Logging

Logs are stored in the `logs` directory with different levels (INFO, WARNING, ERROR) for easy debugging and monitoring.

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License
