# -*- coding: utf-8 -*-
import os
import time
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
    SESSION_SERVER, SESSION_TIMEOUT, WXPAY_CONF
from util.cache import Cache
from util.helper import error, ErrorCode
from util.session import SessionManager
from api import *
from base import AuthHandler, BaseHandler
from util.wx import make_order

tornado.options.define('port', default=8000, help='run on the given port', type=int)
tornado.options.define('debug', default=False, help='debug mode', type=bool)

YOUCAI_WXPAY_CONF = WXPAY_CONF['youcai']


class IndexHandler(AuthHandler):
    @coroutine
    def get(self):
        ua = self.request.headers['User-Agent']
        # hasWx = True if -1 != ua.find('MicroMessenger') else False
        hasWx = 'MicroMessenger' in ua

        state_url = self.get_argument('state', '')  # state 此参数扫码进来 如: http://192.168.1.222:8003/?state=recomitem/15

        if hasWx:  # 微信
            openid = self.session.get('openid')
            if not openid:  # 没有 openid
                code = self.get_argument('code', None)
                if not code:  # 没有 code 获取code
                    redirect_uri = urllib.parse.quote(self.request.protocol + '://' + self.request.host)
                    url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=' + YOUCAI_WXPAY_CONF['appid'] + \
                          '&response_type=code&scope=snsapi_base' \
                          '&redirect_uri=' + redirect_uri \
                          + '&state=' + urllib.parse.quote(state_url) \
                          + '&connect_redirect=1#wechat_redirect'
                    self.redirect(url)
                else:  # 有 code 获取openid
                    client = AsyncHTTPClient()
                    query = {
                        'appid': WXPAY_CONF['youcai']['appid'],
                        'secret': WXPAY_CONF['youcai']['secret'],
                        'code': code,
                        'grant_type': 'authorization_code'
                    }
                    try:
                        response = yield client.fetch(
                            'https://api.weixin.qq.com/sns/oauth2/access_token?' + urllib.parse.urlencode(query))
                        result = json.loads(response.body.decode())
                        # log.info(result)
                        if 'errmsg' in result:
                            log.error(result)
                            return self.write(error(ErrorCode.THIRDERR, result['errmsg']))

                        self.session['openid'] = result['openid']
                        self.session.save()
                    except Exception as e:
                        log.error(e)
                        return self.write(error(ErrorCode.REQERR, '请求openid出错'))

        if state_url:  # 有状态 url 则重定向
            _url = '/#!/' + state_url
            self.redirect(_url)
            return

        self.render('index.html')

    def get_openid(self, code):
        if not code:
            return self.write(error(ErrorCode.PARAMERR, '需要code参数'))

        client = AsyncHTTPClient()
        query = {
            'appid': WXPAY_CONF['youcai']['appid'],
            'secret': WXPAY_CONF['youcai']['secret'],
            'code': code,
            'grant_type': 'authorization_code'
        }
        try:
            response = yield client.fetch(
                'https://api.weixin.qq.com/sns/oauth2/access_token?' + urllib.parse.urlencode(query))
            text = response.body.decode()
            result = json.loads(text)
            if 'errmsg' in result:
                return self.write(error(ErrorCode.THIRDERR, result['errmsg']))
            self.session['openid'] = result['openid']
            self.session.save()
            # return self.write({'openid': result})
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.REQERR, '请求openid出错'))


# class PayHandler(AuthHandler):
#     @coroutine
#     def get(self):
#         if self.userid == 0:
#             return self.write(error(ErrorCode.LOGINERR))
#
#         try:
#             orderno = int(self.get_argument('orderno'))  # 订单号
#         except Exception as e:
#             log.error(e)
#             self.redirect('/')
#             return
#
#         query = {'uid': self.userid, 'orderno': orderno}
#         try:
#             order = yield self.db['youcai'].order.find_one(query)
#         except Exception as exc:
#             log.error(exc)
#             return self.write(error(ErrorCode.DBERR))
#
#         if not order:
#             # 订单不存在
#             self.redirect('/')
#         # self.redirect('/#!pay_result')
#         # return;
#
#         # import random
#         # 支付参数
#         params = make_order(self.session.get('openid'), order['title'], order['orderno'], order['price'] + order['freight'],
#                             self.request.remote_ip)
#         # log.info(params)
#         self.render('pay_weixin.html', params=params)


class PayHandler(AuthHandler):
    def get(self):
        if not self.userid:
            self.redirect('/')
        self.render("pay_weixin.html", params=self.session.get('wx_pay'))


# 有菜优惠券
class CouponHandler(AuthHandler):
    @coroutine
    def get(self):
        self.xsrf_token

        try:
            code = self.get_argument('code', None) or None
            source = self.get_argument('s', '') or ''  # 来源
        except Exception as e:
            log.error(e)
            code = None

        # qmmf:全民免费
        if source not in ['qmmf']:  # 排除无效值
            source = ''

        data = {'msg': '已过期', 'coupons': []}

        if not code:    # code 未传递
            # self.write(error(ErrorCode.UNKOWN, 'code 未传递'))
            self.render('coupon/coupon_error.html', data=data)
            return

        # 验证优惠券包合法性
        try:
            coupon_pack = yield self.db['youcai'].coupon_pack.find_one({'code': code}, {'_id': 0, 'id': 1, 'code': 1, 'remains': 1})
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.SRVERR, '呃，出了点小问题，有菜君正在处理，请稍候再试！'))
            return

        if not coupon_pack: # code 无效
            # self.write(error(ErrorCode.UNKOWN, 'code 无效'))
            self.render('coupon/coupon_error.html', data=data)
            return

        coupons = yield self.db['youcai'].coupon \
            .find({'cpid': coupon_pack['id']}, {'_id': 0, 'uid': 1, 'discount': 1, 'created': 1}).sort(
            [('created', -1)]).to_list(None)
        if coupons:
            for coupon in coupons:
                user = yield self.db['hamlet'].user \
                    .find_one({'id': coupon['uid']}, {'_id': 0, 'nickname': 1, 'mobile': 1, 'headimg': 1})
                coupon['created'] = time.strftime('%Y-%m-%d %X', time.localtime(int(coupon['created']) / 1000))
                coupon['discount'] = int(coupon['discount'] / 100)
                coupon['headimg'] = user['headimg']
                coupon['text'] = '红包的金额和你的颜值一样高哦'
                if user['nickname']:
                    if len(user['nickname']) > 7:
                        coupon['nickname'] = user['nickname'][:6] + '*' * 2
                    else:
                        coupon['nickname'] = user['nickname']
                else:
                    coupon['nickname'] = user['mobile'][:3] + '*' * 6 + user['mobile'][-2:]

        else:
            coupons = []

        if coupon_pack['remains'] <= 0:  # 优惠券已经被抢光
            # self.write(error(ErrorCode.UNKOWN, "优惠券已经被抢光"))
            self.render('coupon/coupon_error.html', data={'msg': '抢光了', 'coupons': coupons})
            return

        # 获取历史优惠券信息
        coupon = {}
        try:
            # self.set_cookie("yc_mobile", '18521592117')
            # cookie_mobile = self.get_secure_cookie("yc_mobile")
            cookie_mobile = self.get_cookie("yc_mobile")
            if cookie_mobile:
                # 获取 uid
                user = yield self.db['hamlet'].user.find_one({'mobile': cookie_mobile}, {'_id': 0, 'id': 1})
                if user:
                    # 获取该批次优惠券
                    coupon = yield self.db['youcai'].coupon \
                        .find_one({'cpid': coupon_pack['id'], 'uid': user['id']},
                                  {'_id': 0, 'id': 1, 'type': 1, 'distype': 1, 'discount': 1, 'charge': 1}
                                  )
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.SRVERR, '呃，出了点小问题，有菜君正在处理，请稍候再试！'))
            return

        if coupon:
            coupon['discount'] = int(coupon['discount']/100)
        else:
            coupon = {}

        self.render('coupon/coupon.html', coupon_pack=coupon_pack, coupon=coupon, data={'coupons': coupons, 'source': source})


# 有菜优惠券说明
class CouponInfoHandler(AuthHandler):
    def get(self):
        self.render('coupon/info.html')


class YoucaiWeb(Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),  # 首页
            # (r'/wx', WxHandler),  # 微信授权页面
            (r'/pay/wx', PayHandler),  # 支付
            # (r'/pay_test', PayWeixinTestHandler),  # 微信支付测试页
            (r'/api/address', address.AddressHandler),
            (r'/api/recom_item', recom_item.DetailHandler),
            (r'/api/home', home.HomeHandler),
            (r'/api/auth/login', auth.LoginHandler),
            (r'/api/order', order.OrderHandler),

            (r'/api/util/smscode', util.SmscodeHandler),
            (r'/api/util/region', util.RegionHandler),

            # (r'/download/yc', YcDownloadHandler),  # 有菜下载
            (r'/coupon', CouponHandler),  # 有菜优惠券
            (r'/api/coupon', coupon.CouponHandler),  # 有菜获取优惠券接口
            (r'/api/update_mobile', coupon.UpdateMobileHandler),  # 更改红包领取手机号
            (r'/coupon/info', CouponInfoHandler),  # 有菜优惠券说明
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
