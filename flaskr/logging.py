
import logging
import sys


def init(name):
    global APP_NAME
    APP_NAME = name

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    filters = [APP_NAME, 'werkzeug']

    for f in filters:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)

        ch.setFormatter(CustomFormatter())
        ch.addFilter(logging.Filter(f))
        logger.addHandler(ch)

    getLogger().info('Initialised logging level=%s',
                     logging.getLevelName(logger.getEffectiveLevel()))


def getLogger(name=None):
    global APP_NAME

    if name:
        log = APP_NAME + '.' + name
    else:
        log = APP_NAME
    return logging.getLogger(log)


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    # {name} {filename}:{lineno}
    format = '[{asctime}] {levelname:<8s} {message}'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, style='{')
        return formatter.format(record)
