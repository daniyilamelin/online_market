Duikt Telegram Shop Bot

Description

A Telegram bot for managing an online store with support for product catalog, orders, and admin panel.
Users can browse products and make purchases directly in Telegram, while administrators can manage the store.

Features

- Product catalog with browsing and purchasing
- Shopping cart and order processing
- Admin panel for managing products
- Interactive keyboards for удобної навігації
- SQLite database for storing products and orders
- Middleware for request processing
- Role-based filters for different user types
- Asynchronous handling using asyncio

Tech Stack

- Python 3.8+
- aiogram / python-telegram-bot
- SQLite
- asyncio

Installation & Run

1. Clone the repository:
   git clone https://github.com/YOUR_USERNAME/tg_bot.git

2. Go to the project folder:
   cd tg_bot

3. Install dependencies:
   pip install -r requirements.txt

4. Create ".env" file:
   BOT_TOKEN=your_telegram_bot_token
   ADMIN_IDS=123456789,987654321
   DATABASE_URL=sqlite:///true_detective.db

5. Run the bot:
   python bot_main.py

How It Works

- Initialization
  The bot connects to the database and registers handlers.

- Request flow
  User request → filters → middleware → handler logic

- Database
  Data is stored in SQLite for fast and reliable access.

- Interaction
  Custom keyboards improve navigation and UX.

- Async processing
  The bot handles multiple requests concurrently using asyncio.

Notes

This project demonstrates backend development skills, working with Telegram Bot API, asynchronous programming, and basic application architecture.
