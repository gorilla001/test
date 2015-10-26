# -*- coding: utf-8 -*-

from tornado.gen import coroutine
from conf.settings import log, IMG_CACHE_URL, IMAGE_DOMAIN
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno


class HomeHandler(AuthHandler):
    @coroutine
    def get(self):
        # if self.userid == 0:
        #     self.write(error(ErrorCode.LOGINERR))
        #     return

        try:
            page = int(self.get_argument('page', 1))
            length = int(self.get_argument('length', None) or 10)

        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.PARAMERR))
            return

        try:
            recom_items = yield self.db['youcai'].recom_item.find({'remains': {'$gt': 0}, 'status': 1}, {'_id': 0}).sort([('type', -1), ('modified', -1)]).skip(
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

class ItemHandler(AuthHandler):
    @coroutine
    def get(self):
        try:
            start = int(self.get_argument('start', 0))
            lastid = int(self.get_argument('lastid', 0))
            length = int(self.get_argument('length', 20))
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.PARAMERR))

        try:  # 推荐菜品
            query = {'remains': {'$gt': 0}, 'status': 1}
            _filter = {'_id': 0, 'created': 0, 'modified': 0}
            if lastid:
                query.update({'id': {'$lt': lastid}})
                items = yield self.db['youcai'].recom_item.find(query, _filter).sort('id', -1).limit(length).to_list(length)
            else:
                sort = [('type', -1), ('modified', -1)]
                items = yield self.db['youcai'].recom_item.find(query, _filter).sort(sort).skip(start).limit(length).to_list(length)

            if self.userid:
                for item in items:
                    if item['type'] == 2:
                        ckey = 'seckill_%d_%d' % (self.userid, item['id'])
                        seckill = self.cache.get(ckey)
                        if not seckill:
                            seckill = yield self.get_seckill_item(self.userid, item['id'])
                            if seckill:
                                self.cache.today(ckey, True)

                        item.update({'bought': True if seckill else False})
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.DBERR))

        if IMG_CACHE_URL:
            for item in items:
                item['imgs'] = list(map(lambda x: IMG_CACHE_URL + x[len(IMAGE_DOMAIN):] if x.startswith(IMAGE_DOMAIN) else x, item['imgs']))

        return self.write({'items': items})

    def get_combo(self, combo_id):
        # Get combo info
        query = {'id': combo_id}
        filters = {'_id': 0}
        try:
            return self.db['youcai'].combo.find_one(query, filters)
        except Exception:
            # NOTE(nmg): raise exception, the caller will catch it
            raise

    def get_combo_items(self, combo_id, issue_no):
        # Get the newest combo items
        query = {'combo_id': combo_id, 'issue_no': issue_no, 'remains': {'$gt': 0}, 'status': 1}
        filters = {'_id': 0, 'created': 0, 'modified': 0}
        sort = [('category', 1), ('modified', -1)]

        try:
            return self.db['youcai'].issue_item.find(query, filters) \
                .sort(sort).to_list(None)
        except Exception:
            # NOTE(nmg): raise exception, the caller will catch it
            raise

    def get_seckill_item(self, uid, item_id):
        query = {'uid': uid, 'siid': item_id}
        try:
            return self.db['youcai'].user_seckill.find_one(query)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))