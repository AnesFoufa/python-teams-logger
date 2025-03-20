import json
import queue
from collections import defaultdict
from logging import Handler, LogRecord, NOTSET, Formatter
from logging.handlers import QueueHandler, QueueListener
from traceback import format_exception
from typing import Iterable

import requests

__all__ = [
    "TeamsHandler",
    "TeamsQueueHandler",
    "Office365CardFormatter",
    "TeamsCardsFormatter",
]


class TeamsCardsFormatter(Formatter):
    """
    This class is the base class for cards formatters.
    https://docs.microsoft.com/en-us/microsoftteams/platform/task-modules-and-cards/what-are-cards
    """

    def format(self, record: LogRecord) -> str:
        raise NotImplementedError()


class TeamsHandler(Handler):
    """
    Logging handler for Microsoft Teams webhook integration.

    This handler blocks operation. Use non-blocking NBTeamsHandler for less
    impact on your application performance.
    """

    def __init__(self, url, level=NOTSET):
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
        try:
            data = self.format(record)
            requests.post(
                url=self.url, headers={"Content-Type": "application/json"}, data=data
            )
        except Exception:
            self.handleError(record)


class TeamsQueueHandler(QueueHandler):
    """
    Non-blocking logging handler for Microsoft Teams webhook integration.

    This handler reduces impact on your application compared to the (blocking)
    TeamsHandler.

    Queue-based implementation from
    https://docs.python.org/3/howto/logging-cookbook.html#dealing-with-handlers-that-block
    """

    def __init__(self, url, level=NOTSET):
        self._log_queue = queue.Queue(-1)
        super().__init__(self._log_queue)

        self._teams_handler = TeamsHandler(url, level)
        teams_log_listener = QueueListener(self._log_queue, self._teams_handler)
        teams_log_listener.start()

    def setFormatter(self, fmt):
        self._teams_handler.setFormatter(fmt)
        super().setFormatter(fmt)


class Office365CardFormatter(TeamsCardsFormatter):
    """
    This formatter formats logs records an Adaptive Card.
    The adaptive card documentation is displayed in the link below:
    https://learn.microsoft.com/en-us/microsoftteams/platform/task-modules-and-cards/cards/cards-reference#adaptive-card
    In addition to the message, each log record attribute (levelname, lineno...etc) can be displayed as facts.
    """

    _facts = {"name", "levelname", "levelno", "lineno"}
    _color_map = defaultdict(
        lambda: "#008000",
        {
            "DEBUG": "#0000FF",  # blue
            "INFO": "#008000",  # green
            "WARNING": "#FFA500",  # orange
            "ERROR": "#FF0000",  # red
            "CRITICAL": "#8B0000",  # darkred
        },
    )

    def __init__(self, facts: Iterable[str]):
        """
        :param facts:  LogRecord attributes to be displayed as facts in the message's card.
        """
        self.facts = self._facts.intersection(set(facts))
        super().__init__()

    def format(self, record: LogRecord) -> str:
        message = record.getMessage()
        exception_details = ""
        has_exception = False

        level_style_map = {
            "DEBUG": "accent",  # blue:light
            "INFO": "good",  # green:light
            "WARNING": "warning",  # yellow/orange:light
            "ERROR": "attention",  # red:light
            "CRITICAL": "attention",  # red:dark (light/dark is set in the card)
        }

        level_style = level_style_map.get(record.levelname, "good")

        if record.exc_info:
            etype, value, tb = record.exc_info
            exception_details = "".join(format_exception(etype, value, tb))
            has_exception = True

        facts = [
            {"title": fact, "value": str(getattr(record, fact))} for fact in self.facts
        ]

        return json.dumps(
            {
                "type": "AdaptiveCard",
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "version": "1.5",
                "body": [
                    {
                        "type": "Container",
                        "style": level_style,
                        "bleed": True,
                        "items": [
                            {
                                "type": "TextBlock",
                                "size": "Medium",
                                "weight": "Bolder",
                                "text": f"{record.levelname.title()} in {record.module}",
                                "wrap": True,
                                "color": (
                                    "dark"
                                    if record.levelname == "CRITICAL"
                                    else "light"
                                ),
                            }
                        ],
                    },
                    {
                        "type": "Container",
                        "style": level_style,
                        "bleed": True,
                        "items": [{"type": "FactSet", "facts": facts}],
                    },
                    {
                        "type": "Container",
                        "style": level_style,
                        "bleed": True,
                        "items": [{"type": "TextBlock", "text": message, "wrap": True}],
                    },
                    {
                        "type": "Container",
                        "style": level_style,
                        "bleed": True,
                        "items": [
                            {
                                "type": "Container",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": exception_details,
                                        "wrap": True,
                                        "fontType": "Monospace",
                                    }
                                ],
                                "$when": has_exception,
                            }
                        ],
                    },
                ],
                "msteams": {"width": "Full"},
            }
        )

    def _build_facts_list(self, record: LogRecord):
        return [{"name": fact, "value": getattr(record, fact)} for fact in self.facts]
