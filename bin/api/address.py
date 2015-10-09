# -*- coding: utf-8 -*-

import re
import json
import time
from tornado.gen import coroutine
from conf.settings import log
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno


class ListHandler(AuthHandler):
    @coroutine
    def get(self):
        if self.userid == 0:
            self.write(error(ErrorCode.LOGINERR))
            return

        try:
            addresses = yield self.db['hamlet'].address.find({'uid': self.userid}, {'_id': 0}).limit(10).to_list(10)
            self.write(addresses)
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR))


class SaveHandler(AuthHandler):
    @coroutine
    def post(self):
        '''修改/增加
        '''
        if self.userid == 0:
            self.write(error(ErrorCode.LOGINERR))
            return

        try:
            address_id = int(self.get_argument('id', None) or 0)
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        try:
            if address_id:
                addresses = yield self.db['hamlet'].address
            self.write()

        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR))