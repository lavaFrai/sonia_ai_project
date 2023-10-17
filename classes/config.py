import json
import logging


class PostgresqlConfig:
    def __init__(self, data):
        self.use = data['use']
        self.url: str = data['url']
        if self.url.startswith('postgres:'):
            self.url = self.url.replace('postgres:', 'postgresql:', 1)


class Config:
    def __init__(self):
        logging.getLogger(__name__).info("Reading config file")

        with open("conf/config.json") as f:
            self.data = json.load(f)

        self.telegram_token = self.data["telegram_token"]
        self.openai_token = self.data["openai_token"]
        self.admin = self.data["admin"]

        self.postgresql = PostgresqlConfig(self.data['postgresql'])
