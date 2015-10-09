# -*- coding: utf-8 -*-

from tornado.gen import coroutine
from conf.settings import log, IMG_CACHE_URL, IMAGE_DOMAIN
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno


class HomeHandler(AuthHandler):
    @coroutine
    def get(self):
        if self.userid == 0:
            self.write(error(ErrorCode.LOGINERR))
            return

        try:
            page = int(self.get_argument('page', 1))
            length = int(self.get_argument('length', None) or 10)

        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        try:
            recom_items = yield self.db['youcai'].recom_item.find({}, {'_id': 0}).sort([('id', -1)]).skip(
                (page - 1) * length).limit(length).to_list(length)
            res = {
                'recom_item_list': []
            }
            if recom_items:
                if IMG_CACHE_URL:
                    for recom_item in recom_items:
                        recom_item['imgs'] = list(map(lambda x: IMG_CACHE_URL + x[len(IMAGE_DOMAIN):] if x.startswith(IMAGE_DOMAIN) else x, recom_item['imgs']))

                res.update({'recom_item_list': recom_items})

            return self.write(res)
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR))
            return
