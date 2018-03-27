import logging as l
import logging.handlers as lh
from os import environ
import queue

LOGGER = l.getLogger()
shutdown = l.shutdown


def _setup_logging() -> (lh.QueueListener, lh.QueueHandler):
    file_formatter = l.Formatter(
        "%(asctime)s [%(threadName)-10.10s] [%(levelname)-5.5s]: %(message)s")
    file_handler = l.FileHandler(environ.get('HOME', '.') + '/.sapfy.log')
    file_handler.setFormatter(file_formatter)

    log_formatter = l.Formatter(
        "%(asctime)s [%(levelname)-5.5s]: %(message)s", datefmt='%H:%M:%S')
    console_handler = l.StreamHandler()
    console_handler.setFormatter(log_formatter)

    log_queue = queue.Queue(-1)
    queue_handler = lh.QueueHandler(log_queue)
    queue_listener = lh.QueueListener(log_queue, console_handler, file_handler)
    LOGGER.addHandler(queue_handler)
    queue_listener.start()
    return queue_listener, queue_handler


LOG_LISTENER, LOG_HANDLER = _setup_logging()
