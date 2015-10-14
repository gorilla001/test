# -*- coding: utf-8 -*-

import time
from tornado.gen import coroutine
from conf.settings import log
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno


class AddressHandler(AuthHandler):
    @coroutine
    def get(self):
        if self.userid == 0:
            return self.write(error(ErrorCode.LOGINERR))

        try:
            docs = yield self.db['hamlet'].address.find(
                {'uid': self.userid},
                {'_id': 0, 'id': 1, 'name': 1, 'mobile': 1, 'city': 1, 'region': 1, 'address': 1, 'default': 1}
            ).sort([('default', -1), ('id', -1)]).limit(5).to_list(5)
            self.write({'addresses': docs})
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR))

    @coroutine
    def post(self):
        if self.userid == 0:
            return self.write(error(ErrorCode.LOGINERR))

        try:
            aid = int(self.get_argument('id', None) or 0)
            name = self.get_argument('name', '')
            mobile = self.get_argument('mobile', '')
            city = self.get_argument('city', '')
            region = self.get_argument('region', '')
            address = self.get_argument('address', '')
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.PARAMERR))

        now = round(time.time() * 1000)
        try:
            if aid:
                data = {}
                if name:
                    data['name'] = name
                if mobile:
                    data['mobile'] = mobile
                if city:
                    data['city'] = city
                if region:
                    data['region'] = region
                if address:
                    data['address'] = address
                if not data:
                    data['default'] = True
                data['modified'] = now

                doc = yield self.db['hamlet'].address.find_and_modify(
                    {'id': aid}, {'$set': data},
                    new=True, fields={'_id': 0, 'city': 1, 'region': 1, 'address': 1})
                if doc:
                    result = doc['city'] + doc['region'] + doc['address']
                else:
                    return self.write(error(ErrorCode.NODATA))

                if data.get('default'):
                    yield self.db['hamlet'].address.update({'uid': self.userid, 'id': {'$ne': aid}},
                                                           {'$set': {'default': False}}, multi=True)
            else:
                aid = mongo_uid('hamlet', 'address')
                yield self.db['hamlet'].address.insert({
                    'id': aid,
                    'uid': self.userid,
                    'name': name,
                    'mobile': mobile,
                    'city': city,
                    'region': region,
                    'street': '',
                    'zid': 0,
                    'zname': '',
                    'building': '',
                    'unit': '',
                    'room': '',
                    'bur': '',
                    'address': address,
                    'default': True,
                    'created': now,
                    'modified': now})
                result = city + region + address
                yield self.db['hamlet'].address.update({'uid': self.userid, 'id': {'$ne': aid}},
                                                       {'$set': {'default': False}}, multi=True)

            try:
                yield self.db['hamlet'].user.update({'id': self.userid}, {'$set': {'address': result}})
                self.session['user'].update({'address': result})
                self.session.save()
            except Exception as e:
                log.error(e)

            self.write({'address': result})
        except Exception as e:
            log.error(e)
            self.write(error(ErrorCode.DBERR))
