teams-logger
===================

Python logging handler for Microsoft Teams web hook integration with simple configuration.

Installation
------------
.. code-block:: bash

    pip install teams-logger

Example
-------
Simple
''''''
.. code-block:: python

  import logging
  from teams_handler import TeamsHandler

  th = TeamsHandler(url='YOUR_WEB_HOOK_URL', level=logging.INFO)
  logging.basicConfig(handlers=[sh])
  logging.warning('warn message')

Using logger
''''''''''''
.. code-block:: python

  import logging
  from teams_handler import TeamsHandler

  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)

  th = TeamsHandler(url='YOUR_WEB_HOOK_URL', level=logging.INFO)
  sh.setLevel(logging.DEBUG)

  logger.debug('debug message')
  logger.info('info message')
  logger.warn('warn message')
  logger.error('error message')
  logger.critical('critical message')
