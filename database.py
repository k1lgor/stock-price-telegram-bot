import json
import logging
import os
from typing import Dict, List, Set

from config import DEFAULT_NOTIFICATION_FREQUENCY, DEFAULT_STOCKS

logger = logging.getLogger(__name__)


class Database:
    """Handles user data storage and retrieval for the stock notification bot."""

    def __init__(self, db_file: str = "user_data.json"):
        """Initialize the database with the specified file.

        Args:
            db_file: Path to the JSON file for storing user data
        """
        self.db_file = db_file
        self.users: Dict[str, Dict] = {}
        self.load_data()

    def load_data(self) -> None:
        """Load user data from the JSON file if it exists."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r") as f:
                    self.users = json.load(f)
                logger.info(
                    f"Loaded data for {len(self.users)} users from {self.db_file}"
                )
            except Exception as e:
                logger.error(f"Error loading database: {e}")
                # Initialize with empty dict if file is corrupted
                self.users = {}

    def save_data(self) -> None:
        """Save user data to the JSON file."""
        try:
            with open(self.db_file, "w") as f:
                json.dump(self.users, f, indent=2)
            logger.info(f"Saved data for {len(self.users)} users to {self.db_file}")
        except Exception as e:
            logger.error(f"Error saving database: {e}")

    def get_user(self, user_id: str) -> Dict:
        """Get user data or create a new entry if user doesn't exist.

        Args:
            user_id: Telegram user ID as string

        Returns:
            User data dictionary
        """
        if user_id not in self.users:
            # Initialize new user with default settings
            self.users[user_id] = {
                "subscribed_stocks": DEFAULT_STOCKS.copy(),
                "notification_frequency": DEFAULT_NOTIFICATION_FREQUENCY,
            }
            self.save_data()
        return self.users[user_id]

    def subscribe_stock(self, user_id: str, stock_symbol: str) -> bool:
        """Subscribe a user to a stock.

        Args:
            user_id: Telegram user ID
            stock_symbol: Stock symbol to subscribe to (e.g., 'AAPL')

        Returns:
            True if newly subscribed, False if already subscribed
        """
        user_data = self.get_user(user_id)
        stock_symbol = stock_symbol.upper()

        if stock_symbol in user_data["subscribed_stocks"]:
            return False

        user_data["subscribed_stocks"].append(stock_symbol)
        self.save_data()
        return True

    def unsubscribe_stock(self, user_id: str, stock_symbol: str) -> bool:
        """Unsubscribe a user from a stock.

        Args:
            user_id: Telegram user ID
            stock_symbol: Stock symbol to unsubscribe from

        Returns:
            True if unsubscribed, False if not subscribed
        """
        user_data = self.get_user(user_id)
        stock_symbol = stock_symbol.upper()

        if stock_symbol not in user_data["subscribed_stocks"]:
            return False

        user_data["subscribed_stocks"].remove(stock_symbol)
        self.save_data()
        return True

    def get_subscribed_stocks(self, user_id: str) -> List[str]:
        """Get list of stocks a user is subscribed to.

        Args:
            user_id: Telegram user ID

        Returns:
            List of stock symbols
        """
        return self.get_user(user_id)["subscribed_stocks"]

    def set_notification_frequency(self, user_id: str, hours: int) -> None:
        """Set notification frequency for a user.

        Args:
            user_id: Telegram user ID
            hours: Notification frequency in hours
        """
        if hours < 1:
            hours = 1  # Minimum 1 hour

        user_data = self.get_user(user_id)
        user_data["notification_frequency"] = hours
        self.save_data()

    def get_notification_frequency(self, user_id: str) -> int:
        """Get notification frequency for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Notification frequency in hours
        """
        return self.get_user(user_id)["notification_frequency"]

    def get_all_users(self) -> List[str]:
        """Get list of all user IDs.

        Returns:
            List of user IDs
        """
        return list(self.users.keys())

    def get_all_subscribed_stocks(self) -> Set[str]:
        """Get set of all unique stocks that any user is subscribed to.

        Returns:
            Set of stock symbols
        """
        all_stocks = set()
        for user_id in self.users:
            all_stocks.update(self.users[user_id]["subscribed_stocks"])
        return all_stocks

    def refresh_default_stocks(self) -> None:
        """Update all users' subscribed stocks when default stocks change.
        This ensures users stay subscribed to the current default stock list.
        """
        for user_id in self.users:
            user_data = self.users[user_id]
            # Add any new default stocks that aren't in the user's list
            for stock in DEFAULT_STOCKS:
                if stock not in user_data["subscribed_stocks"]:
                    user_data["subscribed_stocks"].append(stock)
        self.save_data()
