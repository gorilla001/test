# -*- coding: utf-8 -*-
import logging
import logging.config
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

logging.NOTE = 25
logging.addLevelName(logging.NOTE, "NOTE")


def note(self, message, *args, **kws):
    self._log(logging.NOTE, message, args, **kws)


logging.Logger.note = note
LEVEL_COLOR = {
    logging.DEBUG: '\33[2;39m',
    logging.INFO: '\33[0;37m',
    logging.NOTE: '\033[0;36m',
    logging.WARN: '\33[4;35m',
    logging.ERROR: '\33[5;31m',
    logging.FATAL: '\33[7;31m'
}


class ScreenHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            fs = LEVEL_COLOR[record.levelno] + "%s\n" + '\33[0m'
            try:
                if isinstance(msg, str) and getattr(stream, 'encoding', None):
                    ufs = fs.encode().decode(stream.encoding)
                    try:
                        stream.write(ufs % msg)
                    except UnicodeEncodeError:
                        stream.write((ufs % msg).encode(stream.encoding))
                else:
                    stream.write(fs % msg)
            except UnicodeError:
                stream.write(fs % msg.encode("UTF-8"))

            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class SimpleLog(logging.Handler):
    def __init__(self, filename, mode='sized', max_bytes=0, backup_count=0):
        logging.Handler.__init__(self)
        if mode == 'timed':
            self._handler = TimedRotatingFileHandler(filename, 'midnight', 1, backup_count)
        else:
            self._handler = RotatingFileHandler(filename, 'a', max_bytes, backup_count)

    def emit(self, record):
        self._handler.emit(record)

    def setFormatter(self, fmt):
        self._handler.setFormatter(fmt)

    def close(self):
        self._handler.close()


class SingleLevelFilter(logging.Filter):
    def __init__(self, passlevel, reject=False):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return record.levelno != self.passlevel
        else:
            return record.levelno == self.passlevel


def initlog(config, console=False, mode='sized', max_bytes=536870912, backup_count=10, separate=True):
    conf = {
        'version': 1,
        'formatters': {
            'myformat': {
                'format': '%(asctime)s %(process)d,%(threadName)s %(filename)s:%(lineno)d [%(levelname)s] %(message)s'
            }
        },
        'filters': {
            'debug': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.DEBUG
            },
            'info': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.INFO
            },
            'note': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.NOTE
            },
            'warn': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.WARN
            },
            'error': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.ERROR
            },
            'critical': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.CRITICAL
            }
        },
        'handlers': {
            'console': {
                'class': 'util.logger.ScreenHandler',
                'formatter': 'myformat',
                'level': 'DEBUG',
                'stream': 'ext://sys.stdout'
            }
        },
        'root': {
            'level': 'DEBUG'
        }
    }

    handlers = ['console'] if console else []
    for level, name in config.items():
        handler = '%s_FILE' % level
        handlers.append(handler)
        conf['handlers'][handler] = {
            'class': 'util.logger.SimpleLog',
            'formatter': 'myformat',
            'level': level.upper(),
            'filename': name,
            'mode': mode,
            'max_bytes': max_bytes,
            'backup_count': backup_count,
            'filters': [level.lower()] if separate else None
        }

    conf['root'].update({'handlers': handlers})
    logging.config.dictConfig(conf)
    return logging.getLogger()
