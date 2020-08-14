import unittest.mock
from logging import Handler, INFO, getLogger

from teams_logger import __version__, TeamsHandler


class TestVersion(unittest.TestCase):
    def test(self):
        self.assertEqual('0.1.0', __version__)


class TestTeamsHandler(unittest.TestCase):
    url = "http://fakeurl/"
    level = INFO
    log_text = "bla bla"

    def test_is_handler(self):
        assert issubclass(TeamsHandler, Handler)

    def test_properties(self):
        handler = TeamsHandler(url=self.url, level=self.level)
        assert self.url == handler.url
        assert self.level == handler.level

    @unittest.mock.patch("requests.post")
    def test_emit(self, mock_requests):
        mock_requests.post = unittest.mock.MagicMock()
        logger = getLogger(__name__)
        logger.setLevel(INFO)
        handler = TeamsHandler(self.url, level=INFO)
        logger.addHandler(handler)
        logger.info(self.log_text)
        mock_requests.assert_called_with(self.url, json={"text": self.log_text})


if __name__ == '__main__':
    unittest.main()
