import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiohttp import web
from dotenv import load_dotenv

from handlers.user_private import user_router
from handlers.admin_private import admin_private_router
from common.bot_comands_list import private
from bot_main import TOKEN

load_dotenv()

if not TOKEN:
    raise ValueError("❌ Не знайдено токен!")

# ----------------------
# 🌐 Веб-сервер
# ----------------------
async def handle_root(request):
    uptime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"<h1>✅ Bot is Running!</h1><p>⏰ Time: {uptime}</p>"
    return web.Response(text=html, content_type='text/html')

async def handle_health(request):
    return web.json_response({"status": "ok", "bot": "running", "timestamp": datetime.now().isoformat()})

async def handle_ping(request):
    return web.Response(text="pong")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/ping", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Веб-сервер запущено на порту {port}")


# ----------------------
# 🤖 Telegram бот
# ----------------------
ALLOWED_UPDATES = ["message", "callback_query", "edited_message", "inline_query"]

async def on_startup(bot: Bot):
    print("="*50)
    print("🚀 Запуск бота...")
    await bot.set_my_commands(private, scope=types.BotCommandScopeAllPrivateChats())
    print("✅ Команди встановлено")
    print("✅ Бот готовий до роботи!")
    print("="*50)

async def on_shutdown(bot: Bot):
    print("\n🛑 Зупинка бота...")
    await bot.session.close()
    print("👋 До побачення!")

async def start_bot(bot: Bot, dp: Dispatcher):
    await on_startup(bot)
    try:
        await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES, drop_pending_updates=True)
    finally:
        await on_shutdown(bot)


# ----------------------
# 🔗 Головна функція
# ----------------------
async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(admin_private_router)
    dp.include_router(user_router)

    # Паралельний запуск веб-сервера і бота
    web_task = asyncio.create_task(start_web_server())
    bot_task = asyncio.create_task(start_bot(bot, dp))

    await asyncio.gather(web_task, bot_task)


# ----------------------
# 🔹 Запуск через явний event loop
# ----------------------
if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 Зупинено користувачем")
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
        raise




