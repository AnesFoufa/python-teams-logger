import io
import json
import sys
import time
import unittest.mock
from logging import Handler, INFO, WARNING, getLogger, LogRecord, shutdown
from logging.config import dictConfig

from teams_logger import TeamsHandler, TeamsQueueHandler, Office365CardFormatter


class FakeCode(object):
    def __init__(self, co_filename, co_name):
        self.co_filename = co_filename
        self.co_name = co_name


class FakeFrame(object):
    def __init__(self, f_code, f_globals):
        self.f_code = f_code
        self.f_globals = f_globals


class FakeTraceback(object):
    def __init__(self, frames, line_nums):
        if len(frames) != len(line_nums):
            raise ValueError("Ya messed up!")
        self._frames = frames
        self._line_nums = line_nums
        self.tb_frame = frames[0]
        self.tb_lineno = line_nums[0]

    @property
    def tb_next(self):
        if len(self._frames) > 1:
            return FakeTraceback(self._frames[1:], self._line_nums[1:])


class FakeException(Exception):
    def __init__(self, *args, **kwargs):
        self._tb = None
        super().__init__(*args, **kwargs)

    @property
    def __traceback__(self):
        return self._tb

    @__traceback__.setter
    def __traceback__(self, value):
        self._tb = value

    def with_traceback(self, value):
        self._tb = value
        return self


class TestOffice365CardFormatter(unittest.TestCase):
    facts_parameter = ["name"]
    expected_facts_in_message_card = [{
        "name": "name",
        "value": "logger"
    }]

    @classmethod
    def setUpClass(cls) -> None:
        cls.formatter = Office365CardFormatter(facts=cls.facts_parameter)

    def test_format(self):
        log_record = LogRecord(
            name="logger", level=INFO,
            pathname=__name__, lineno=1, msg="hello %s",
            args=("world",), exc_info=None)

        expected_formatted_message_card = {
            "@context": "https://schema.org/extensions",
            "@type": "MessageCard",
            "sections": [{
                "facts": self.expected_facts_in_message_card
            }],
            "summary": "hello world",
            "text": "hello world",
            "title": "Info in __main__",
            "themeColor": "#008000"
        }

        formatted_message_card = self.formatter.format(log_record)
        self.assert_cards_equal(expected_formatted_message_card,
                                json.loads(formatted_message_card))

    def test_tb_format(self):
        """
        https://stackoverflow.com/questions/19248784/faking-a-traceback-in-python
        https://docs.microsoft.com/en-us/python/api/azureml-automl-core/azureml.automl.core.shared.fake_traceback?view=azure-ml-py
        https://github.com/elifiner/pydump/blob/master/pydump.py
        poetry add --dev pydump
        pip install pydump ?
        """
        code1 = FakeCode("made_up_filename.py", "non_existent_function")
        code2 = FakeCode("another_non_existent_file.py", "another_non_existent_method")
        frame1 = FakeFrame(code1, {})
        frame2 = FakeFrame(code2, {})
        tb = FakeTraceback([frame1, frame2], [1, 3])
        exc_info = FakeException, None, tb

        log_record = LogRecord(
            name="logger", level=INFO,
            pathname=__name__, lineno=1, msg="hello %s",
            args=("world",), exc_info=exc_info)

        formatted_message_card = self.formatter.format(log_record)

        expected = {
            "@context": "https://schema.org/extensions",
            "@type": "MessageCard",
            "title": "Info in __main__",
            "summary": "hello world",
            "sections": [{"facts": self.expected_facts_in_message_card}],
            "themeColor": "#008000",
            "text": "hello world\n\n"
                    "<code>Traceback (most recent call last):\n"
                    "  File \"made_up_filename.py\", line 1, in non_existent_function\n"
                    "  File \"another_non_existent_file.py\", line 3, in another_non_existent_method\nNoneType: None\n"
                    "</code>"
        }
        self.assert_cards_equal(expected,
                                json.loads(formatted_message_card))

    def assert_cards_equal(self, expected_card, actual_card):
        """
        Reorder the facts before sorting the cards.
        """
        expected_facts: list = expected_card["sections"][0]["facts"]
        expected_facts.sort(key=lambda x: x["name"])
        actual_facts = actual_card["sections"][0]["facts"]
        actual_facts.sort(key=lambda x: x["name"])
        self.assertEqual(expected_card, actual_card)


class TestOffice365CardFormatter2(TestOffice365CardFormatter):
    facts_parameter = ["name", "levelname", "lineno"]
    expected_facts_in_message_card = [{
        "name": "name",
        "value": "logger"
    }, {
        "name": "lineno",
        "value": 1
    }, {
        "name": "levelname",
        "value": "INFO"
    }]


class TestTeamsHandler(unittest.TestCase):
    url = 'https://outlook.office.com/webhook/fake_id/IncomingWebhook/fake_id'
    level = INFO
    log_text = "bla bla %s"
    log_parameter = "foo"
    log_level = INFO
    fake_message_card = "fake message card"

    @classmethod
    def setUpClass(cls) -> None:
        log_message = cls.log_text % cls.log_parameter
        cls.expected_payload_with_default_formatter = json.dumps({
            "text": log_message
        })

    def setUp(self) -> None:
        self.teams_handler = TeamsHandler(url=self.url, level=self.level)
        self.teams_handler.formatter = None
        self.logger = getLogger(__name__)
        self.logger.setLevel(self.level)
        self.logger.handlers = [self.teams_handler]

        self.logging_dict = {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'msteams': {
                    'level': WARNING,
                    'class': 'teams_logger.TeamsHandler',
                    'url': self.url,
                },
            },
            'loggers': {
                __name__: {
                    'handlers': ['msteams'],
                    'level': self.level,
                }
            },
        }

    def test_is_handler(self):
        assert issubclass(TeamsHandler, Handler)

    def test_properties(self):
        handler = TeamsHandler(url=self.url, level=self.level)
        assert self.url == handler.url
        assert self.level == handler.level

    @unittest.mock.patch("requests.post")
    def test_emit_with_default_formatter(self, mock_requests):
        self.logger.log(self.log_level, self.log_text, self.log_parameter)
        mock_requests.assert_called_with(url=self.url, headers={"Content-Type": "application/json"},
                                         data=self.expected_payload_with_default_formatter)

    @unittest.mock.patch("requests.post")
    def test_emit_exception(self, mock_requests):
        mock_requests.side_effect = ValueError()
        sys.stderr = io.StringIO()  # disable output of handleError operation
        try:
            self.logger.log(self.log_level, self.log_text, self.log_parameter)
        except ValueError:
            self.fail(
                "An exception was raised; it should have been suppressed by the logging handler")
        finally:
            sys.stderr = sys.__stderr__  # restore stderr

    @unittest.mock.patch("requests.post")
    def test_emit_with_teams_message_card_formatter(self, mock_requests):
        teams_message_card_formatter = Office365CardFormatter(facts=[])
        teams_message_card_formatter.format = unittest.mock.MagicMock(return_value=self.fake_message_card)
        self.teams_handler.setFormatter(teams_message_card_formatter)
        self.logger.log(self.log_level, self.log_text, self.log_parameter)
        mock_requests.assert_called_with(url=self.url, headers={"Content-Type": "application/json"},
                                         data=self.fake_message_card)

    def test_initializing_logger_from_dict(self):
        dictConfig(self.logging_dict)
        self.logger = getLogger(__name__)

        self.assertEqual(1, len(self.logger.handlers))
        handler = self.logger.handlers[0]
        self.assertIsInstance(handler, TeamsHandler)
        self.assertEqual(self.url, handler.url)
        self.assertEqual(WARNING, handler.level)

    @unittest.mock.patch("requests.post")
    def test_dict_level_handling(self, mock_requests):
        """ Test correctly handling logging levels when initialized from dict """
        dictConfig(self.logging_dict)
        self.logger = getLogger(__name__)

        # Logging to same level (WARNING) should be handled
        self.logger.log(WARNING, self.log_text, self.log_parameter)
        mock_requests.assert_called_with(url=self.url,
                                         headers={
                                             "Content-Type": "application/json"},
                                         data=self.expected_payload_with_default_formatter)

        # Logging to lower level (INFO) should *not* be handled
        mock_requests.reset_mock()
        self.logger.log(INFO, self.log_text, self.log_parameter)
        mock_requests.assert_not_called()


class TestTeamsQueueHandler(unittest.TestCase):
    url = 'https://outlook.office.com/webhook/fake_id/IncomingWebhook/fake_id'
    level = INFO
    log_text = "bla bla %s"
    log_parameter = "foo"
    log_level = INFO

    @classmethod
    def setUpClass(cls) -> None:
        log_message = cls.log_text % cls.log_parameter
        cls.expected_payload_with_default_formatter = json.dumps({
            "text": log_message
        })

    def setUp(self) -> None:
        self.handler = TeamsQueueHandler(url=self.url)
        self.handler.setLevel(self.level)
        self.handler.formatter = None
        self.logger = getLogger(__name__)
        self.logger.setLevel(self.level)
        self.logger.handlers = [self.handler]

    def tearDown(self) -> None:
        # Clean up logging resources, to avoid deadlock at
        # acquiring lock in other tests
        shutdown()

    def test_is_handler(self):
        assert issubclass(TeamsQueueHandler, Handler)

    @unittest.mock.patch("requests.post")
    def test_emit_with_default_formatter(self, mock_requests):
        mock_requests.reset_mock()
        self.logger.log(self.log_level, self.log_text, self.log_parameter)
        # Call to Teams is handled in separate thread,
        # so wait until we have a signal it's processed
        count = 0
        while not self.handler._log_queue.empty():
            time.sleep(0.1)
            count += 1
            if count >= 10:
                self.fail("Log queue not processed in reasonable time")
        mock_requests.assert_called_with(url=self.url, headers={"Content-Type": "application/json"},
                                         data=self.expected_payload_with_default_formatter)


if __name__ == '__main__':
    unittest.main()
