import json
import logging


class Config:
    def __init__(self):
        logging.getLogger(__name__).info("Reading config file")

        with open("conf/config.json") as f:
            self.data = json.load(f)

        self.telegram_token = self.data["telegram_token"]
        self.openai_token = self.data["openai_token"]
        self.admin = self.data["admin"]
