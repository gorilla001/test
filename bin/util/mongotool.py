# -*- coding: utf-8 -*-
import time
import gridfs
import pymongo


def get_methods(*objs):
    return set(attr for obj in
               objs for attr in
               dir(obj) if not attr.startswith('_') and hasattr(getattr(obj, attr), '__call__'))

EXECUTABLE_MONGO_METHODS = get_methods(pymongo.MongoClient, pymongo, gridfs.GridFS, gridfs)


class Executable:
    def __init__(self, method, logger, wait_time=None):
        self.method = method
        self.logger = logger
        self.wait_time = wait_time or 60

    def __call__(self, *args, **kwargs):
        start = time.time()
        i = 0
        while True:
            try:
                return self.method(*args, **kwargs)
            except pymongo.errors.AutoReconnect:
                end = time.time()
                delta = end - start
                if delta >= self.wait_time:
                    break
                self.logger.warning('AutoReconnecting, try %d (%.1f seconds)'
                                    % (i, delta))
                time.sleep(pow(2, i))
                i += 1

        return self.method(*args, **kwargs)

    def __dir__(self):
        return dir(self.method)

    def __str__(self):
        return self.method.__str__()

    def __repr__(self):
        return self.method.__repr__()


class MongoProxy:
    def __init__(self, conn, logger=None, wait_time=None):
        if logger is None:
            import logging
            logger = logging.getLogger(__name__)

        self.conn = conn
        self.logger = logger
        self.wait_time = wait_time

    def __getitem__(self, key):
        item = self.conn[key]
        if hasattr(item, '__call__'):
            return MongoProxy(item, self.logger, self.wait_time)
        return item

    def __getattr__(self, key):
        attr = getattr(self.conn, key)
        if hasattr(attr, '__call__'):
            if key in EXECUTABLE_MONGO_METHODS:
                return Executable(attr, self.logger, self.wait_time)
            else:
                return MongoProxy(attr, self.logger, self.wait_time)
        return attr

    def __call__(self, *args, **kwargs):
        return self.conn(*args, **kwargs)

    def __dir__(self):
        return dir(self.conn)

    def __str__(self):
        return self.conn.__str__()

    def __repr__(self):
        return self.conn.__repr__()

    def __nonzero__(self):
        return True


def safe_mongocall(call):
    def _safe_mongocall(*args, **kwargs):
        for i in range(5):
            try:
                return call(*args, **kwargs)
            except pymongo.errors.AutoReconnect:
                time.sleep(pow(2, i))

        raise RuntimeError('Failed AutoReconnect!')

    return _safe_mongocall
