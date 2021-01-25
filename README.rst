teams-logger
===================

Python logging handler for Microsoft Teams webhook integration with both simple and dictionary configurations.

Installation
------------
.. code-block:: bash

    pip install teams-logger

Examples
--------
Simple configuration
''''''''''''''''''''
.. code-block:: python

  import logging
  from teams_logger import TeamsHandler

  th = TeamsHandler(url='YOUR_WEB_HOOK_URL', level=logging.INFO)
  logging.basicConfig(handlers=[th])
  logging.warning('warn message')

Simple configuration and non blocking handler
'''''''''''''''''''''''''''''''''''''''''''''
.. code-block:: python

  import logging
  from teams_logger import TeamsQueueHandler
  th = TeamsQueueHandler(url='YOUR_WEB_HOOK_URL', level=logging.INFO)
  logging.basicConfig(handlers=[th])
  logging.info("info message")

Simple configuration and Card Formatter
'''''''''''''''''''''''''''''''''''''''
.. code-block:: python

  import logging
  from teams_logger import TeamsHandler, Office365CardFormatter

  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)

  th = TeamsHandler(url='YOUR_WEB_HOOK_URL', level=logging.INFO)
  th.setLevel(logging.DEBUG)
  logger.addHandler(th)

  cf = Office365CardFormatter(facts=["name", "levelname", "lineno"])
  th.setFormatter(cf)
  logger.debug('debug message')
  logger.info('info message')
  logger.warning('warning message')
  logger.error('error message')
  logger.critical('critical message')

  try:
      2/0
  except ZeroDivisionError as e:
      logger.error('Oops !', exc_info=True)

Dictionary configuration and Card Formatter
'''''''''''''''''''''''''''''''''''''''''''
.. code-block:: python

  import logging
  import logging.config
  from teams_logger import TeamsHandler, Office365CardFormatter

  url = 'YOUR_WEB_HOOK_URL'
  logging_dict = {
      'version': 1, 
      'disable_existing_loggers': False,
      'formatters': {
          'teamscard': {
              '()': Office365CardFormatter,
              'facts': ["name", "levelname", "lineno"],
          },
      },
      'handlers': {
          'msteams': {
              'level': logging.INFO,
              'class': 'teams_logger.TeamsHandler',
              'url': url,
              'formatter': 'teamscard',
          },
      },
      'loggers': {
          __name__: {
              'handlers': ['msteams'],
              'level': logging.DEBUG,
          }
      },
  }
  logging.config.dictConfig(logging_dict)
  logger = logging.getLogger(__name__)
  logger.info('Info message')
