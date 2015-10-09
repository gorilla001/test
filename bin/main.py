# -*- coding: utf-8 -*-
import os
import time
import motor
import json
import tornado.escape
import tornado.ioloop
import tornado.options
from tornado.gen import coroutine
from tornado.options import options
from tornado.web import authenticated, Application
from conf.settings import CACHE_SERVER, log, MONGO_STORE, MONGO_HAMLET, MONGO_YOUCAI, ROOT_PATH, SESSION_SECRET, \
    SESSION_SERVER, SESSION_TIMEOUT
from util.cache import Cache
from util.helper import check_password
from util.session import SessionManager
from api import *
from base import AuthHandler, BaseHandler
from util.helper import error, ErrorCode

tornado.options.define('port', default=8000, help='run on the given port', type=int)
tornado.options.define('debug', default=False, help='debug mode', type=bool)


class IndexHandler(AuthHandler):
    @coroutine
    def get(self):
        self.xsrf_token
        self.render('index.html')


class ProfileHandler(AuthHandler):
    @coroutine
    @authenticated
    def get(self):
        op = self.session['op']

        firm_name = {'name': 'ALL'}
        zone_name = {'name': 'ALL'}

        self.render('profile.html', op=op, firm_name=firm_name['name'], zone_name=zone_name['name'], title='个人信息')


class HelpHandler(AuthHandler):
    @authenticated
    def get(self):
        op = self.session['op']
        self.render('help.html', op=op, title='帮助')


class YoucaiWeb(Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),  # 首页
            (r'/api/address/list', address.ListHandler),
            (r'/api/address/save', address.SaveHandler),
            (r'/api/recom_item/detail', recom_item.DetailHandler),
            (r'/api/home', home.HomeHandler),
            (r'/api/auth/send_smscode', auth.SendSmscodeHandler),
            (r'/api/auth/login', auth.LoginHandler),
        ]
        settings = dict(
            debug=options.debug,
            xsrf_cookies=True,
            login_url='/login',
            cookie_secret='alA9P3tIUGFe3boFVM2A2tmusiRsrTGdgm8Vrk=',
            static_path=os.path.join(ROOT_PATH, 'static') if options.debug else os.path.join(os.path.dirname(ROOT_PATH),
                                                                                             'static'),
            template_path=os.path.join(ROOT_PATH, 'templates'),
            db={'hamlet': motor.MotorClient(MONGO_HAMLET['master']).hamlet,
                'store': motor.MotorClient(MONGO_STORE['master']).store,
                'youcai': motor.MotorClient(MONGO_YOUCAI['master']).youcai},
            cache=Cache(CACHE_SERVER),
            session_manager=SessionManager(SESSION_SECRET, SESSION_SERVER, SESSION_TIMEOUT, not options.debug)
        )
        super(YoucaiWeb, self).__init__(handlers, **settings)


def start():
    tornado.options.parse_command_line()
    YoucaiWeb().listen(options.port, xheaders=True)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    print("run on port %s" % options.port)
    start()
