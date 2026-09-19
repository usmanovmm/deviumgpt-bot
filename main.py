import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
import google.generativeai as genai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("DeviumGPT")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.getenv("PORT", 8080))

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise RuntimeError("Ошибка: Переменные TELEGRAM_BOT_TOKEN или GEMINI_API_KEY не заданы на Render.")

SYSTEM_INSTRUCTION = (
    "Вы — DeviumGPT, официальный интеллектуальный ассистент, разработанный технологическим агентством Devium Tech. "
    "Предоставляйте точные, структурированные и профессиональные ответы. Помогайте пользователям в решении их задач."
)

async def handle_health_check(_request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)

async def setup_health_server(port: int) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    app.router.add_get("/health", handle_health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner

async def main() -> None:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-3.8-flash",
        system_instruction=SYSTEM_INSTRUCTION,
    )

    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def handle_start(message: types.Message) -> None:
        greeting = (
            "🚀 **DeviumGPT** — интеллектуальный ассистент от **Devium Tech**.\n\n"
            "Задайте любой вопрос или опишите задачу, и я подготовлю решение."
        )
        await message.answer(greeting)

    @dp.message()
    async def handle_prompt(message: types.Message) -> None:
        if not message.text:
            return

        await bot.send_chat_action(chat_id=message.chat.id, action="typing")

        try:
            response = await asyncio.to_thread(model.generate_content, message.text)
            if response.text:
                await message.answer(response.text)
            else:
                await message.answer("Запрос обработан, но ответ пуст. Попробуйте переформулировать.")
        except Exception as err:
            logger.error("Error processing request: %s", err, exc_info=True)
            await message.answer("⚠️ Не удалось обработать запрос. Попробуйте снова через некоторое время.")

    health_runner = await setup_health_server(PORT)
    logger.info("Health check endpoint listening on port %d", PORT)

    try:
        logger.info("Starting bot polling loop...")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down resources...")
        await health_runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application stopped gracefully.")
