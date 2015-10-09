# -*- coding: utf-8 -*-
import time
import msgpack
import redis


class Cache(object):
    def __init__(self, redis_options):
        self.redis = redis.StrictRedis(redis_options['host'], redis_options['port'],
                                       redis_options['db'], redis_options['password'])

    def get(self, key, decoder=None):
        value = self.redis.get(key)
        if value:
            value = msgpack.loads(value, object_pairs_hook=decoder, encoding='utf-8')

        return value

    def set(self, key, value, minutes=None):
        self.redis.set(key, msgpack.dumps(value), minutes * 60 if minutes else None)

    def today(self, key, value):
        now = time.localtime()
        midnight = time.mktime(now[:3] + (0, 0, 0) + now[6:])
        self.redis.set(key, msgpack.dumps(value), int(midnight + 86400 - time.time()))

    def delete(self, key):
        self.redis.delete(key)
