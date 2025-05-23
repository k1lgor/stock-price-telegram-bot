# Changelog

All notable changes to the Stock Price Notification Bot will be documented in this file.

## [0.4.0] - 2024-04-27

### Added

- Implemented self-ping feature to keep the server alive on Render.com (pings every 14 minutes)
- Updated scheduler to send stock notifications every 2 hours by default
- Improved documentation for deployment on Render.com

### Changed

- `/check` command now shows all subscribed stocks if used without arguments

## [0.3.0] - 2024-05-15

### Added

- Implemented webhook support to avoid conflicts with Telegram polling
- Added fallback to polling mode for local development
- Improved application startup and shutdown process
- Enhanced error handling for webhook mode

## [0.2.0] - 2024-01-25

### Added

- Added web server for health checks on Render deployment
- Improved error handling for stock updates
- Enhanced logging for better debugging
- Added support for asynchronous web server

## [0.1.0] - 2024-01-17

### Added

- Initial release of the Stock Price Notification Bot
- Real-time stock monitoring using Yahoo Finance API
- Telegram bot interface with command handlers
- Periodic stock price notifications (default: 2 hours)
- User subscription management for stocks
- Stock price checking commands (/check, /check all)
- Customizable notification frequency
- Default stock list management (/updatestocks)
- Comprehensive error handling and logging
- Docker support for containerized deployment
- Database persistence for user preferences
- Asynchronous scheduling using APScheduler

### Features

- `/start` - Welcome message and command overview
- `/subscribe SYMBOL` - Subscribe to specific stocks
- `/unsubscribe SYMBOL` - Unsubscribe from stocks
- `/check SYMBOL` - Check current stock price
- `/check all` - Check all subscribed stocks
- `/list` - View subscribed stocks
- `/frequency HOURS` - Set notification frequency
- `/updatestocks SYMBOL1 SYMBOL2 ...` - Update default stock list
- `/help` - Display help information

### Dependencies

- python-telegram-bot ^20.6
- yfinance ^0.2.31
- apscheduler ^3.10.4
- python-dotenv ^1.0.0
- requests ^2.31.0
