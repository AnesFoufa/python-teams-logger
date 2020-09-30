teams-logger
===================

Python logging handler for Microsoft Teams web hook integration with simple configuration.

Installation
------------
.. code-block:: bash

    pip install teams-logger

Examples
--------
Simple
''''''
.. code-block:: python

  import logging
  from teams_logger import TeamsHandler

  th = TeamsHandler(url='YOUR_WEB_HOOK_URL', level=logging.INFO)
  logging.basicConfig(handlers=[th])
  logging.warning('warn message')


Using Card Formatter
''''''''''''''''''''
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



Using dict configuration
''''''''''''''''''''''''
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
