# -*- coding: utf-8 -*-

from tornado.gen import coroutine
from conf.settings import log
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno


class DetailHandler(AuthHandler):
    @coroutine
    def get(self):
        if self.userid == 0:
            self.write(error(ErrorCode.LOGINERR))
            return

        try:
            recom_item_id = int(self.get_argument('id'))
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        try:
            recom_item = yield self.db['youcai'].recom_item.find_one({'id': recom_item_id}, {'_id': 0})
            if recom_item:
                return self.write(recom_item)
            else:
                return self.write(error(ErrorCode.NODATA))
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DATAERR))
            return
