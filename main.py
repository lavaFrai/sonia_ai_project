import asyncio
import logging
from classes.server import Server


logging.basicConfig(level=logging.DEBUG)

server = Server()

if __name__ == "__main__":
    asyncio.run(server.run())
