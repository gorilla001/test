# -*- coding: utf-8 -*-
import time
import random
from hashlib import md5
from tornado.gen import coroutine
from conf.settings import log, GRAVATAR_URL
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid


class SendSmscodeHandler(AuthHandler):
    @coroutine
    def post(self):
        '''
        接受手机号，发送验证码
        '''
        try:
            mobile = self.get_argument('mobile')
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        result = self.cache.get(mobile)
        if result:
            seconds = round(time.time()) - result['time']
            if seconds < 60:
                return self.write(error(ErrorCode.REQERR, '请稍等%d秒重新发送' % (60 - seconds)))

        code = '%06d' % random.randint(0, 999999)
        content = "有菜手机验证码： {code}".format(code=code)
        try:
            self.sms(mobile, content)
            log.info('send sms: %s, %s' % (mobile, content))
        except Exception as e:
            log.error('send sms failed: %s, %s, %s' % (mobile, content, e))

        self.cache.set(mobile, {'code': code, 'time': round(time.time())}, 5)
        self.write({})


class CouponHandler(AuthHandler):
    @coroutine
    def post(self):
        '''
        用户输入手机号，获取优惠券
        参数：
            mobile：
            code：
            smscode（可选）
        '''
        try:
            mobile = self.get_argument('mobile', None)
            code = self.get_argument('code', None)
            smscode = self.get_argument('smscode', None)
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        # 验证码是否存在，是它第一次还是第二次请求的标志
        if smscode:
            cache_smscode = self.cache.get(mobile)
            if not cache_smscode or smscode != cache_smscode.get('code'):
                self.write(error(ErrorCode.CODEERR))
                return

        now = round(time.time() * 1000)
        try:
            coupon_pack = yield self.db['youcai'].coupon_pack.find_one({'code': code}, {'_id': 0})

            if not coupon_pack:  # 优惠券包无效
                self.write(error(ErrorCode.UNKOWN, '优惠券包不存在'))
                return

            if coupon_pack['expire'] <= now:  # 优惠券包已过期
                self.write(error(ErrorCode.UNKOWN, '优惠券已过期'))
                return

            if coupon_pack['remains'] <= 0:
                self.write(error(ErrorCode.UNKOWN, "优惠券已经被抢光"))
                return

            # 该手机号对应的用户是否存在，不存在则插入user表
            user = yield self.db['hamlet'].user.find_one({'mobile': mobile}, {'_id': 0, 'id': 1})

            if user:  # 老用户
                # 不管怎么样，只要用户存在，获取优惠券就正常进行
                user_id = user['id']
                coupon = yield self.db['youcai'].coupon.find_one({'uid': user_id, 'cpid': coupon_pack['id']},
                                                                 {'_id': 0, 'id': 1, 'type': 1, 'distype': 1,
                                                                  'discount': 1, 'charge': 1})
                if coupon:
                    # 用户手机号存放在 cookie中
                    self.set_cookie("yc_mobile", mobile)
                    self.write({'coupon': coupon})
                    return
            else:  # 新用户
                # 用户不存在，则进行判断是否有验证码，
                # 有     ：则是验证码已经通过，继续往下走
                # 没有   ：则发验证码，
                if smscode:  # 注册 并 领取红包
                    user_id = mongo_uid('hamlet', 'user')
                    user_doc = {
                        'id': user_id,
                        'unionid': None,
                        'openid': None,
                        'name': None,
                        'nickname': None,
                        'sex': 0,
                        'mobile': mobile,
                        'role': 0,
                        'province': None,
                        'city': None,
                        'address': None,
                        'headimg': GRAVATAR_URL.format(hash=md5(('SQC%d' % user_id).encode()).hexdigest()),
                        'bgimg': None,
                        'hometown': None,
                        'career': None,
                        'hobby': None,
                        'proverb': None,
                        'birthday': None,
                        'cid': 0,
                        'rid ': 0,
                        'zid': 0,
                        'ozid': 0,
                        'zname': None,
                        'coins': 100,
                        'oid': 0,
                        'password': '',
                        'lastlat': None,
                        'lastlng': None,
                        'lastip': None,
                        'status': 0,
                        'offline': False,
                        'created': now,
                        'modified': now}
                    yield self.db['hamlet'].user.insert(user_doc)
                else:
                    # TODO -发-验-证-码-

                    # 改动 --> 不发送验证码，只是单纯的告诉前端，你需要获取验证
                    self.write(error(ErrorCode.NOUSER, '您还不是有菜用户，请注册领取红包'))
                    return

            # 优惠券包剩余数量减1
            ret = yield self.db['youcai'].coupon_pack.find_and_modify({'code': code}, {'$inc': {'remains': -1}},  new=True, fields={'_id': 0, 'remains': 1})
            if ret['remains'] == 0:
                yield self.db['youcai'].order.update({'orderno': coupon_pack['orderno']}, {'$set': {'cpflag': False}})

            # 添加一条优惠券
            discount = random.randint(coupon_pack['minpar'], coupon_pack['maxpar'])
            discount -= discount % 100
            coupon_doc = {
                'id': mongo_uid('youcai', 'coupon'),
                'cpid': coupon_pack['id'],
                'uid': user_id,
                'type': coupon_pack['type'],
                'distype': 1,
                'discount': discount,
                'charge': coupon_pack['charge'],
                'used': False,
                'expire': now + 2592000000,  # 2592000000 = 30 * 24 * 60 * 60 * 1000,
                'created': now
            }
            yield self.db['youcai'].coupon.insert(coupon_doc)

            # 用户手机号存放在 cookie中
            self.set_cookie("yc_mobile", mobile)
            # self.set_secure_cookie("yc_mobile", mobile)

            return self.write({
                'coupon': {
                    'cpid': coupon_doc['cpid'],
                    'type': coupon_doc['type'],
                    'distype': coupon_doc['distype'],
                    'discount': coupon_doc['discount'],
                    'charge': coupon_doc['charge']
                }
            })

        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR, '呃，出了点小问题，有菜君正在处理，请稍候再试！'))
            return


# 更改红包领取手机号
class UpdateMobileHandler(AuthHandler):
    def post(self):
        try:
            mobile = self.get_argument('mobile', None)
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return
        self.set_cookie("yc_mobile", mobile)
        self.write({})

