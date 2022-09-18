import asyncio

from bot import dispatcher

if __name__ == '__main__':
    asyncio.run(dispatcher.start_polling())