import json
from logging import Handler, LogRecord
from typing import Iterable

import requests

__all__ = ["TeamsHandler", "Office365CardFormatter", "TeamsCardsFormatter"]


class TeamsCardsFormatter:
    """
    This class is the base class for cards formatters.
    https://docs.microsoft.com/en-us/microsoftteams/platform/task-modules-and-cards/what-are-cards
    """
    def format(self, record: LogRecord) -> str:
        raise NotImplementedError()


class TeamsHandler(Handler):
    """
    Logging handler for Microsoft Teams webhook integration.
    """
    def __init__(self, url, level):
        """
        :param url: Microsoft Teams incoming webhook url.
        :param level: Logging level (INFO, DEBUG, ERROR...etc)
        """
        super().__init__(level=level)
        self.url = url

    def format(self, record: LogRecord) -> str:
        if not isinstance(self.formatter, TeamsCardsFormatter):
            return json.dumps({"text": super().format(record)})
        else:
            return self.formatter.format(record)

    def emit(self, record: LogRecord):
        data = self.format(record)
        requests.post(url=self.url, headers={"Content-Type": "application/json"}, data=data)


class Office365CardFormatter(TeamsCardsFormatter):
    """
    This formatter formats logs records as a simple office 365 connector card.
    The connector card documentation is displayed in the link below:
    https://docs.microsoft.com/en-us/microsoftteams/platform/task-modules-and-cards/cards/cards-reference#office-365-connector-card
    In addition to the message, each log record attribute (levelname, lineno...etc) can be displayed as facts.
    """
    _facts = {"name", "levelname", "levelno", "lineno"}

    def __init__(self, facts: Iterable[str]):
        """
        :param facts:  LogRecord attributes to be displayed as facts in the message's card.
        """
        self.facts = self._facts.intersection(set(facts))
        super().__init__()

    def format(self, record: LogRecord) -> str:
        return json.dumps({
            "@context": "https://schema.org/extensions",
            "@type": "MessageCard",
            "sections": [
                {
                    "facts": self._build_facts_list(record)
                }
            ],
            "text": record.getMessage()
        })

    def _build_facts_list(self, record: LogRecord):
        return [{
            "name": fact,
            "value": getattr(record, fact)
        } for fact in self.facts]
