import logging
from datetime import datetime
from typing import Dict, List, Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class StockService:
    """Service for fetching and processing stock data using Yahoo Finance API."""

    @staticmethod
    def get_stock_info(symbol: str) -> Optional[Dict]:
        """Get current stock information for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Dictionary containing stock information or None if error occurs
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            # Get current price and day's change
            current_price = info.get("currentPrice")
            previous_close = info.get("previousClose")

            if not current_price or not previous_close:
                logger.error(f"Could not get price data for {symbol}")
                return None

            price_change = current_price - previous_close
            price_change_percent = (price_change / previous_close) * 100

            return {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "current_price": current_price,
                "previous_close": previous_close,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "volume": info.get("volume"),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    @staticmethod
    def get_multiple_stocks_info(symbols: List[str]) -> Dict[str, Dict]:
        """Get current stock information for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their stock information
        """
        results = {}
        for symbol in symbols:
            info = StockService.get_stock_info(symbol)
            if info:
                results[symbol] = info
        return results

    @staticmethod
    def format_stock_message(stock_info: Dict) -> str:
        """Format stock information into a readable message.

        Args:
            stock_info: Dictionary containing stock information

        Returns:
            Formatted message string
        """
        symbol = stock_info["symbol"]
        name = stock_info["name"]
        price = stock_info["current_price"]
        change = stock_info["price_change"]
        change_percent = stock_info["price_change_percent"]
        currency = stock_info["currency"]

        # Format the message with emojis based on price change
        emoji = "📈" if change >= 0 else "'📉"
        sign = "+" if change >= 0 else ""

        message = f"{emoji} {name} ({symbol})\n"
        message += f"Price: {currency} {price:.2f}\n"
        message += f"Change: {sign}{change:.2f} ({sign}{change_percent:.2f}%)\n"

        return message

    @staticmethod
    def validate_stock_symbol(symbol: str) -> bool:
        """Validate if a stock symbol exists and can be fetched.

        Args:
            symbol: Stock symbol to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return "regularMarketPrice" in info
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
