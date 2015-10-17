# -*- coding: utf-8 -*-

import random
import time
from hashlib import md5
from tornado.gen import coroutine
from conf.settings import log, GRAVATAR_URL
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno


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
            user = yield self.db['hamlet'].user.find_one({'mobile': mobile}, {'_id': 0})
            if not user:            # 新用户
                user_id = mongo_uid('hamlet', 'user')
                user = {
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
                yield self.db['hamlet'].user.insert(user)

                self.save_userid(user['id'])
                del user['_id']
                self.session['op'] = user
            else:
                self.save_userid(user['id'])
                self.session['op'] = user
            self.session.save()

            # 获取用户地址列表
            address_list = yield self.db['hamlet'].address.find({'uid': self.userid}, {'_id': 0, 'id': 1, 'default': 1, 'name': 1, 'mobile': 1, 'city': 1, 'region': 1, 'address': 1}).sort([('default', -1), ('id', 1)]).limit(10).to_list(10)
            
            op = {
                'id': user['id'],
                'mobile': user['mobile'],
                'name': user['name'],
                'nickname': user['nickname']
            }
            return self.write({'user': op, 'address_list': address_list})

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