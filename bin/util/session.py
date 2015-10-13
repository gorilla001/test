# -*- coding: utf-8 -*-
import hashlib
import hmac
import uuid
import msgpack
import redis


class SessionData(dict):
    def __init__(self, session_id, hmac_key):
        self.session_id = session_id
        self.hmac_key = hmac_key


class Session(SessionData):
    def __init__(self, session_manager, request_handler):
        self.session_manager = session_manager
        self.request_handler = request_handler

        try:
            current_session = session_manager.get(request_handler)
        except InvalidSessionException:
            current_session = session_manager.get()
        for key, data in current_session.items():
            self[key] = data

        self.session_id = current_session.session_id
        self.hmac_key = current_session.hmac_key

    def save(self):
        self.session_manager.set(self.request_handler, self)

    def remove(self):
        self.session_manager.remove(self.request_handler, self)
        self.clear()


class SessionManager(object):
    def __init__(self, secret, redis_options, session_timeout, secure):
        self.secret = secret
        self.session_timeout = session_timeout
        self.secure = secure
        self.redis = redis.StrictRedis(redis_options['host'], redis_options['port'],
                                       redis_options['db'], redis_options['password'])

    def _fetch(self, session_id):
        try:
            session_data = self.redis.get(session_id)
            if session_data is not None:
                self.redis.expire(session_id, self.session_timeout)
                session_data = msgpack.loads(session_data, encoding='utf-8')

            if type(session_data) is dict:
                return session_data
            else:
                return {}
        except IOError:
            return {}

    def get(self, request_handler=None):
        if request_handler is None:
            session_id = None
            hmac_key = None
        else:
            session_id = request_handler.get_secure_cookie('sid').decode()
            hmac_key = request_handler.get_secure_cookie('skey').decode()

        if session_id is None:
            session_exists = False
            session_id = self._generate_id()
            hmac_key = self._generate_hmac(session_id)
        else:
            session_exists = True

        check_hmac = self._generate_hmac(session_id)
        if hmac_key != check_hmac:
            raise InvalidSessionException()

        session = SessionData(session_id, hmac_key)
        if session_exists:
            session_data = self._fetch(session_id)
            for key, data in session_data.items():
                session[key] = data

        return session

    def set(self, request_handler, session):
        if self.secure:
            request_handler.set_secure_cookie('sid', session.session_id, httponly=True, secure=True)
            request_handler.set_secure_cookie('skey', session.hmac_key, httponly=True, secure=True)
        else:
            request_handler.set_secure_cookie('sid', session.session_id, httponly=True)
            request_handler.set_secure_cookie('skey', session.hmac_key, httponly=True)

        session_data = msgpack.dumps(dict(session.items()))
        self.redis.setex(session.session_id, self.session_timeout, session_data)

    def remove(self, request_handler, session):
        self.redis.delete(session.session_id)
        request_handler.clear_all_cookies()

    def _generate_id(self):
        new_id = hashlib.sha1((self.secret + uuid.uuid4().hex).encode())
        return new_id.hexdigest().encode()

    def _generate_hmac(self, session_id):
        return hmac.new(session_id, self.secret.encode(), hashlib.sha1).hexdigest().encode()


class InvalidSessionException(Exception):
    pass
