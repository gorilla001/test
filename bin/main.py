# -*- coding: utf-8 -*-
import os
import json
import motor
import urllib.parse
import tornado.escape
import tornado.ioloop
import tornado.options
from tornado.gen import coroutine
from tornado.options import options
from tornado.web import Application
from tornado.httpclient import AsyncHTTPClient
from conf.settings import CACHE_SERVER, log, MONGO_STORE, MONGO_HAMLET, MONGO_YOUCAI, ROOT_PATH, SESSION_SECRET, \
    SESSION_SERVER, SESSION_TIMEOUT, WXPAY_CONF, WX_CONF
from util.cache import Cache
from util.helper import error, ErrorCode
from util.session import SessionManager
from api import *
from base import AuthHandler, BaseHandler
from util.test import make_order

tornado.options.define('port', default=8000, help='run on the given port', type=int)
tornado.options.define('debug', default=False, help='debug mode', type=bool)

YOUCAI_WXPAY_CONF = WXPAY_CONF['youcai']


class IndexHandler(AuthHandler):
    @coroutine
    def get(self):
        self.xsrf_token

        self.get_openid(self.get_argument('code', None) or '')
        self.render('index.html')

    def get_openid(self, code):
        if not code:
            return self.write(error(ErrorCode.PARAMERR, '需要code参数'))

        client = AsyncHTTPClient()
        query = {
            'appid': WX_CONF['appid'],
            'secret': WX_CONF['secret'],
            'code': code,
            'grant_type': 'authorization_code'
        }
        try:
            response = yield client.fetch(
                'https://api.weixin.qq.com/sns/oauth2/access_token?' + urllib.parse.urlencode(query))
            text = response.body.decode()
            log.info(text)
            result = json.loads(text)
            log.info(result)
            if 'errmsg' in result:
                log.error(result)
                return self.write(error(ErrorCode.THIRDERR, result['errmsg']))
            self.session['openid'] = result['openid']
            self.session.save()
            # return self.write({'openid': result})
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.REQERR, '请求openid出错'))


# 微信入口
class WxHandler(AuthHandler):
    def get(self):
        redirect_uri = urllib.parse.quote(self.request.protocol + '://' + self.request.host)
        # url = urllib.parse.quote('https://youcai.shequcun.com')
        url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=' + YOUCAI_WXPAY_CONF['appid'] + \
              '&redirect_uri=' + redirect_uri \
              + '&response_type=code&scope=snsapi_base&state=STATE&connect_redirect=1#wechat_redirect'
        self.redirect(url)


class PayWeixinHandler(AuthHandler):
    # @coroutine
    def get(self):
        # 支付参数
        import random

        params = make_order(self, "测试支付", random.randint(1000000000000, 9999999999999), 1, self.request.remote_ip)
        log.error(params)
        self.render('pay_weixin.html', params=params)


class PayWeixinTestHandler(AuthHandler):
    # @coroutine
    def get(self):
        try:
            # 支付参数
            import random

            params = make_order(self, "测试支付", random.randint(1000000000000, 9999999999999), 1, self.request.remote_ip)
            log.error(params)
            self.render('pay_weixin_test.html', params=params)
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.PARAMERR))


class YoucaiWeb(Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),  # 首页
            (r'/wx', WxHandler),  # 微信授权页面
            # (r'/pay/weixn_test', PayWeixinTestHandler),  # 微信支付测试页
            (r'/pay_test', PayWeixinTestHandler),  # 微信支付测试页
            (r'/api/address/list', address.ListHandler),
            (r'/api/address/save', address.SaveHandler),
            (r'/api/recom_item/detail', recom_item.DetailHandler),
            (r'/api/home', home.HomeHandler),
            (r'/api/auth/send_smscode', auth.SendSmscodeHandler),
            (r'/api/auth/login', auth.LoginHandler),
            (r'/api/order', order.OrderHandler)
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
