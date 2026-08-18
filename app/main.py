from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.config import Settings


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    asyncio.run(dp.start_polling(bot, settings=settings))


if __name__ == "__main__":
    main()
