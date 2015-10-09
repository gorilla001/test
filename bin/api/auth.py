# -*- coding: utf-8 -*-

import random
import time
from hashlib import md5
from tornado.gen import coroutine
from conf.settings import log, GRAVATAR_URL
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno


class SendSmscodeHandler(AuthHandler):
    @coroutine
    def post(self):
        '''接受手机号，发送验证码
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


class LoginHandler(AuthHandler):
    @coroutine
    def post(self):
        try:
            mobile = self.get_argument('mobile')
            smscode = self.get_argument('smscode')

        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        now = round(time.time()) * 1000

        smscode_check = self.cache.get(mobile)
        if not smscode_check:
            return self.write(error(ErrorCode.CODEXPIRE))
        if smscode != smscode_check.get('code'):
            return self.write(error(ErrorCode.CODEERR))

        try:
            user = yield self.db['youcai'].user.find_one({'mobile': mobile}, {'_id': 0})
            if not user:            # 新用户
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

                self.save_userid(user_doc['id'])
                del user_doc['_id']
                self.session['op'] = user_doc
            else:
                self.save_userid(user['id'])
                self.session['op'] = user
            self.session.save()
            return self.write({'login': True})

        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR))
            return


class LogoutHandler(AuthHandler):
    @coroutine
    def post(self):
        if self.userid:
            self.session.remove()
        return self.write({'logout': True})