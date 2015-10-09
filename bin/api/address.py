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

        now = round(time.time()) * 1000
        try:
            address_id = int(self.get_argument('id', None) or 0)
            address_doc = {
                'name': self.get_argument('name'),
                'mobile': self.get_argument('mobile'),
                'city': self.get_argument('city'),
                'region': self.get_argument('region'),
                'street': self.get_argument('street', ''),
                'zname': self.get_argument('zname'),
                'building': self.get_argument('building'),
                'unit': self.get_argument('unit', ''),
                'room': self.get_argument('room'),
                'modified': now
            }
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        try:
            if address_id:      # 修改
                yield self.db['hamlet'].address.find_and_modify({'id': address_id}, {'$set': address_doc})
            else:               # 添加
                address_doc.update({'id': mongo_uid('hanlet', 'address'),
                                    'uid': self.userid,
                                    'created': now,
                                    'zid': 0})      # TODO
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR))
            return