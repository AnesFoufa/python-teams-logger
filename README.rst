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

  cf = Office365CardFormatter(facts=["name", "levelane", "lineno"])
  th.setFormatter(cf)
  logger.debug('debug message')
  logger.info('info message')
  logger.warning('warning message')
  logger.error('error message')
  logger.critical('critical message')
