# -*- coding: utf-8 -*-

import random
import time
from tornado.gen import coroutine
from conf.settings import log
from base import AuthHandler, BaseHandler, unblock
from util.helper import error, ErrorCode, streamtype


class SmscodeHandler(AuthHandler):
    @coroutine
    def post(self):
        '''接受手机号，发送验证码
        '''
        try:
            mobile = self.get_argument('mobile')
            if not mobile:
                return self.write(error(ErrorCode.PARAMERR))

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


class RegionHandler(AuthHandler):
    @coroutine
    def get(self):
        try:
            pid = int(self.get_argument('pid', -1))
            rrange = int(self.get_argument('range', 1))
            rtype = int(self.get_argument('type', 0))
            start = max(int(self.get_argument('start', 0)), 0)
            length = int(self.get_argument('length', 50))
            group = int(self.get_argument('group', 0))
            if pid == -1 and rtype == 2 and group:
                start = 0
                length = 1000
            else:
                group = 0
                length = min(max(int(length), 1), 100)
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        query = {'status': 1} if rrange == 1 else {}
        if pid != -1:
            query.update({'pid': pid})
        elif rtype:
            if rtype == 2:
                query.update({'type': rtype})
            else:
                query.update({'pid': 0})

        try:
            result = []
            if group:
                result = self.cache.get('group_city')
            if not result:
                result = yield self.db['hamlet'].region.find(query, {'_id': 0, 'id': 1, 'name': 1, 'isleaf': 1}).sort('priority', 1).skip(start).limit(length).to_list(length)
                if group:
                    self.cache.today('group_city', result)

            self.write({'regions': result})
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR))
