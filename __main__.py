import asyncio

from loguru import logger

from bot import dispatcher

if __name__ == '__main__':
    logger.info("Starting...")
    asyncio.run(dispatcher.start_polling())