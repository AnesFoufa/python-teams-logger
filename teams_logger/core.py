from logging import Handler

import requests

__all__ = ["TeamsHandler"]


class TeamsHandler(Handler):
    def __init__(self, url, level):
        self.url = url
        super().__init__(level=level)

    def emit(self, record):
        message = self.format(record)
        requests.post(self.url, json={"text": message})
