# -*- coding: utf-8 -*-
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from tornado.ioloop import IOLoop
from tornado.options import options
from tornado.web import asynchronous, RequestHandler
from conf.settings import log, CPU_COUNT, SMS_SERVER
from util.helper import json_dumps
from util.session import Session
from util.thriftclient import ThriftClient

EXECUTOR = ThreadPoolExecutor(max_workers=CPU_COUNT)


def unblock(f):
    @asynchronous
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        EXECUTOR.submit(partial(f, *args, **kwargs)).add_done_callback(lambda future: IOLoop.instance().add_callback(partial(callback, future)))

        def callback(future):
            self.write(future.result())
            self.finish()

    return wrapper


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        self.start = time.time()
        self.userid = 0
        self.errcode = 0
        self.response = None

        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.db = self.settings['db']
        self.sms = lambda mobile, content, sender='YOUCAI_WX', client=ThriftClient(SMS_SERVER['thrift'], SMS_SERVER['hosts']): client.call('sendsms', sender, [mobile] if isinstance(mobile, str) else mobile, content)

    def write(self, chunk):
        if isinstance(chunk, (dict, list, tuple)):
            if 'errcode' in chunk:
                self.errcode = chunk['errcode']

            chunk = json_dumps(chunk)
            self.set_header('Content-Type', 'application/json; charset=UTF-8')
            # self.set_header('Access-Control-Allow-Origin', '*')
            # self.set_header('Access-Control-Allow-Headers', 'X-Requested-With')
            self.response = chunk[:253] + '...' if len(chunk) > 256 else chunk
        else:
            ct = self._headers['Content-Type']
            if isinstance(ct, bytes):
                ct = ct.decode()

            self.response = '<%s>' % ct.split(';')[0]

        super(BaseHandler, self).write(chunk)

    def on_finish(self):
        queries = self.request.query_arguments
        if '_xsrf' in queries:
            queries.pop('_xsrf')

        bodies = self.request.body_arguments
        if '_xsrf' in bodies:
            bodies.pop('_xsrf')
        if 'mobile' in bodies:
            mobile = bodies['mobile'][0]
            bodies['mobile'] = mobile[:3] + b'*' * 4 + mobile[-4:]
        if 'password' in bodies:
            password = bodies['password'][0]
            bodies['password'] = password[:1] + b'*' * (len(password) - 2) + password[-1:]
        if 'account' in bodies:
            account = bodies['account'][0]
            bodies['account'] = account[:4] + b'*' * (len(account) - 8) + account[-4:]
        if 'idcard' in bodies:
            idcard = bodies['idcard'][0]
            bodies['idcard'] = idcard[:4] + b'*' * (len(idcard) - 8) + idcard[-4:]

        log.note('userid=%d|ip=%s|method=%s|path=%s|query=%s|body=%s|code=%d|errcode=%d|time=%.3f|ua=%s|resp=%s' %
                 (self.userid, self.request.remote_ip, self.request.method, self.request.path,
                  queries, bodies, self._status_code, self.errcode, (time.time() - self.start) * 1000,
                  self.request.headers.get('User-Agent', ''), self.response or ''))

        self.errcode = 0
        self.response = None


class AuthHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        super(AuthHandler, self).__init__(application, request, **kwargs)
        self.cache = self.settings['cache']
        self.session = Session(self.settings['session_manager'], self)
        self.save_userid()

    def get_current_user(self):
        return self.session.get('userid')

    def save_userid(self, userid=None):
        if userid:
            self.userid = int(userid)
            self.session['userid'] = self.userid
            self.session.save()
        else:
            self.userid = self.session.get('userid') or 0

        if options.debug:
            self.set_cookie("uid", str(self.userid), expires_days=30, httponly=True)
        else:
            self.set_cookie("uid", str(self.userid), expires_days=30, httponly=True, secure=True)
