# -*- coding: utf-8 -*-

import re
import rsa
import time
import base64
import datetime
from tornado.gen import coroutine
from conf.settings import log
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno

_DATABASE = 'youcai'
YOUCAI_WXPAY_CONF = WXPAY_CONF['youcai']
PRI_KEY = rsa.PrivateKey.load_pkcs1(base64.decodebytes(ALIPAY_CONF['private_key']), 'DER')

_ORDER_TYPE = {
    1: "套餐订单",
    2: "选菜订单",
    3: "单品订单",
    4: "自动选菜订单",
}

_COUPON_TYPE = {
    1: "套餐优惠券",
    2: "单品优惠券",
}


class ItemNotFoundError(Exception):
    def __init__(self, item):
        self.item = item

    def __str__(self):
        return "no such item {}".format(self.item)


class OrderHandler(AuthHandler):
    @coroutine
    def post(self):
        if self.userid == 0:
            return self.write(error(ErrorCode.LOGINERR))

        try:
            combo_id = int(self.get_argument('combo_id', 0))  # 套餐订单，选菜订单必传，套餐订单不传items和extras
            order_type = int(self.get_argument('type'))  # 订单类型
            combo_idx = int(self.get_argument('combo_idx', 0))  # 子订单序号
            raw_items = self.get_argument('items', None)  # 选菜订单必传，格式：id1:amount1,id2:amount2...
            raw_extras = self.get_argument('extras', None)  # 选菜订单可选，单品订单必传，格式：id1:amount1,id2:amount2...
            spares = self.get_argument('spares', None)  # 备选菜,格式：id1, id2, id3...
            coupon_id = int(self.get_argument('coupon_id', None) or 0)
            name = self.get_argument('name')
            mobile = self.get_argument('mobile')
            address = self.get_argument('address')
            memo = self.get_argument('memo', '')
            paytype = int(self.get_argument('paytype', None) or 2)
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.PARAMERR))

        if not order_type:
            log.error("order type must be specified")
            return self.write(error(ErrorCode.PARAMERR))

        if not name or not mobile or not address:
            log.error("name or mobile or address must specified")
            return self.write(error(ErrorCode.PARAMERR))

        if order_type == 1:
            # if not combo_id or combo_idx is None:
            #     log.error("combo id or idx must be specified")
            #     return self.write(error(ErrorCode.PARAMERR))
            if not combo_id:
                log.error("combo_id must be specified")
                return self.write(error(ErrorCode.PARAMERR))

            if not raw_items:  # empty combo order
                log.error("没有选菜")
                return self.write(error(ErrorCode.PARAMERR))
            else:  # combo with items
                if not raw_extras:  # combo with items no extras
                    combo = yield self.get_combo_info(combo_id)
                    if not combo:
                        log.error("no such combo {}".format(combo_id))
                        return self.write(error(ErrorCode.NODATA, '套餐不存在'))

                    oid = mongo_uid(_DATABASE, 'order')
                    order_no = gen_orderno(oid)  # used for alipay also
                    combo_order_no = order_no
                    order_type = 1
                    try:
                        price = self.get_combo_price(combo, combo_idx)
                    except IndexError:
                        return self.write(self.write(error(ErrorCode.DBERR)))

                    status = 0
                    times = 1
                    title = combo['title']  # used for alipay only
                    item_type = 1

                    yield self.create_order(oid, order_no, combo_order_no, order_type, item_type, price, status, times,
                                            combo, combo_idx, name, mobile, address, memo)

                    items_list = raw_items.split(',')
                    if not self.validate_items(items_list):
                        log.error("raw items format error")
                        return self.write(error(ErrorCode.PARAMERR))

                    try:
                        yield self.add_items(order_no, items_list)
                    except ItemNotFoundError as exc:
                        log.error(exc)
                        return self.write(error(ErrorCode.NODATA, '要购买的菜品在数据库找不到'))

                else:
                    combo = yield self.get_combo_info(combo_id)
                    if not combo:
                        log.error("no such combo {}".format(combo_id))
                        return self.write(error(ErrorCode.NODATA, '套餐不存在'))

                    oid = mongo_uid(_DATABASE, 'order')
                    order_no = gen_orderno(oid)  # used for alipay also
                    combo_order_no = order_no
                    order_type = 1
                    status = 0
                    times = 1
                    title = combo['title']  # used for alipay only
                    item_type = 1

                    raw_extras_list = raw_extras.split(',')
                    if not self.validate_items(raw_extras_list):
                        log.error("raw items format error")
                        return self.write(error(ErrorCode.PARAMERR))

                    try:
                        price = yield self.get_extras_price(raw_extras_list)
                    except ItemNotFoundError as exc:
                        log.error(exc)
                        return self.write(error(ErrorCode.NODATA, '要购买的菜品在数据库找不到'))

                    yield self.create_order(oid, order_no, combo_order_no, order_type, item_type, price, status, times,
                                            combo, combo_idx, name, mobile, address, memo)

                    try:
                        yield self.add_extras(order_no, raw_extras_list)
                    except ItemNotFoundError as exc:
                        log.error(exc)
                        return self.write(error(ErrorCode.NODATA, '要购买的菜品在数据库找不到'))

                    raw_items_list = raw_items.split(',')
                    if not self.validate_items(raw_items_list):
                        log.error("raw items format error")
                        return self.write(error(ErrorCode.PARAMERR))

                    try:
                        yield self.add_items(order_no, raw_items_list)
                    except ItemNotFoundError as exc:
                        log.error(exc)
                        return self.write(error(ErrorCode.NODATA, '要购买的菜品在数据库找不到'))

                if spares:
                    spares_list = spares.split(',')
                    spares_item = []
                    for sp in spares_list:
                        try:
                            sp_obj = yield self.db[_DATABASE].issue_item.find_one({'id': int(sp)}, {'_id': 0})
                        except Exception as exc:
                            log.error(exc)
                            return self.write(error(ErrorCode.DBERR))

                        if not sp_obj:
                            log.error("no such spares item {}".format(sp))
                            return self.write(error(ErrorCode.PARAMERR))
                        spare_title = sp_obj['title']
                        img = sp_obj['imgs'][0]
                        now = round(time.time() * 1000)
                        oid = mongo_uid(_DATABASE, 'order_spare')

                        item = {'id': oid,
                                'ssid': sp,
                                'orderno': order_no,
                                'title': spare_title,
                                'img': img,
                                'created': now,
                                'modified': now}

                        spares_item.append(item)

                    try:
                        yield self.db[_DATABASE].order_spare.insert(spares_item)
                    except Exception as exc:
                        log.error(exc)
                        return self.write(error(ErrorCode.DBERR))
        elif order_type == 2:
            if not combo_id or not raw_items:
                log.error("combo_id or raw_items must be specified")
                return self.write(error(ErrorCode.PARAMERR))

            combo = yield self.get_combo_info(combo_id)
            if not combo:
                log.error("no such combo {}".format(combo_id))
                return self.write(error(ErrorCode.NODATA, '套餐不存在'))

            # duration = combo['duration']
            # max_times = len(shipday) * duration
            title = combo['title']  # used for alipay only
            order_info = yield self.get_order_info(self.userid, combo_id)
            try:
                order_times = len(order_info)
            except (TypeError, IndexError):
                return self.write(error(ErrorCode.DBERR, "无法判定已经配送的次数"))

            duration = combo['duration']
            ship_times = len(combo['shipday'])
            total_times = duration * ship_times
            if order_times >= total_times:
                return self.write(error(ErrorCode.REQERR, "套餐配送次数已购"))

            combo_order = yield self.get_combo_order(self.userid, combo_id)

            combo_order_no = combo_order['orderno']
            times = order_times + 1
            combo_idx = combo_order['combo_idx']
            shipday_weekday = combo['shipday'][0]
            now = datetime.datetime.now()
            today = datetime.datetime(now.year, now.month, now.day)
            delta = shipday_weekday - today.isoweekday()
            shipday = today + datetime.timedelta(days=7 + delta if delta < 0 else delta)
            left_day = shipday + datetime.timedelta(days=-7)
            right_day = shipday + datetime.timedelta(days=-1)
            created = order_info[0]['created'] / 1000
            if left_day.timestamp() <= created < right_day.timestamp():
                return self.write(error(ErrorCode.DATAEXIST, "今天您已经选过菜了"))

            try:
                last_delay = yield self.db[_DATABASE].order_delay.find(
                    {'orderno': combo_order_no},
                    {'_id': 0, 'times': 1, 'date': 1}).sort([('id', -1)]).limit(1).to_list(1)
            except Exception as exc:
                log.error(exc)
                return self.write(error(ErrorCode.DBERR))

            next_shipday = shipday + datetime.timedelta(days=7)
            next_date = round(next_shipday.timestamp() * 1000)
            if last_delay and next_date == last_delay[0]['date']:
                return self.write(error(ErrorCode.REQERR, "已延期不能选菜"))

            oid = mongo_uid(_DATABASE, 'order')
            order_no = gen_orderno(oid)  # used for alipay also
            order_type = 2
            price = 0
            status = 1
            item_type = 1

            yield self.create_order(oid, order_no, combo_order_no, order_type, item_type, price, status, times,
                                    combo, combo_idx, name, mobile, address, memo)

            raw_items_list = raw_items.split(',')
            if not self.validate_items(raw_items_list):
                log.error("raw items format error")
                return self.write(error(ErrorCode.PARAMERR))

            try:
                yield self.add_items(order_no, raw_items_list)
            except ItemNotFoundError as exc:
                log.error(exc)
                return self.write(error(ErrorCode.NODATA, '要购买的菜品在数据库找不到'))
        elif order_type == 3:
            if not raw_extras:
                log.error("raw extras can't be null")
                return self.write(error(ErrorCode.PARAMERR))

            oid = mongo_uid(_DATABASE, 'order')
            order_no = gen_orderno(oid)  # used for alipay also
            combo_order_no = 0
            order_type = 3
            status = 0
            times = 0
            item_type = 2

            raw_extras_list = raw_extras.split(',')
            for item in raw_extras_list:
                match = re.match(r"^(\d+)\:(\d+)$", item)
                item_id = int(match.group(1))
                item_obj = yield self.get_recom_item(item_id)
                if not item_obj:
                    raise ItemNotFoundError(item_id)

                item_obj = item_obj[0]
                recom_type = item_obj['type']
                if recom_type == 2:  # 秒杀
                    item_type = 3
                    ckey = 'seckill_%d_%d' % (self.userid, item_id)
                    seckill = self.cache.get(ckey)
                    if not seckill:
                        seckill = yield self.get_seckill_item(self.userid, item_id)
                    if seckill:
                        return self.write(error(ErrorCode.DATAEXIST, '您已经秒杀过该商品,不能重复秒杀!'))

                    yield self.add_seckill_item(self.userid, item_id)
                    self.cache.today(ckey, True)
            try:
                price = yield self.get_extras_price(raw_extras_list)
            except ItemNotFoundError as exc:
                log.error(exc)
                return self.write(error(ErrorCode.NODATA, '要购买的菜品在数据库找不到'))

            title = yield self.get_extras_title(raw_extras_list)
            combo, combo_idx = None, None
            yield self.create_order(oid, order_no, combo_order_no, order_type, item_type, price, status, times,
                                    combo, combo_idx, name, mobile, address, memo, title)

            try:
                yield self.add_extras(order_no, raw_extras_list)
            except ItemNotFoundError as exc:
                log.error(exc)
                return self.write(error(ErrorCode.NODATA, '要购买的菜品在数据库找不到'))
        else:
            return self.write(error(ErrorCode.PARAMERR))

        result = {'orderno': order_no}
        if price != 0:
            disprice = price
            if coupon_id != 0:
                try:
                    coupon = yield self.db[_DATABASE].coupon.find_one({'id': coupon_id, 'uid': self.userid})
                except Exception as exc:
                    log.error(exc)
                    return self.write(error(ErrorCode.DBERR))

                if not coupon:
                    log.error("优惠券不存在{}".format(coupon_id))
                    return self.write(error(ErrorCode.REQERR, '非法请求'))

                if (order_type == 1 and coupon['type'] == 2) or (order_type == 3 and coupon['type'] == 1):
                    log.error("优惠卷类型不匹配， 订单类型{} 优惠券类型{}".format(
                        _ORDER_TYPE[order_type],
                        _COUPON_TYPE[coupon['type']])
                    )
                    return self.write(error(ErrorCode.REQERR, '非法请求'))

                if coupon['used']:
                    return self.write(error(ErrorCode.DATAEXIST, '优惠券已使用过'))

                if round(time.time() * 1000) > coupon['expire']:
                    return self.write(error(ErrorCode.CODEXPIRE, '优惠券已过期'))

                if coupon['distype'] == 1:
                    discount = coupon['discount']
                    disprice = 0 if (price - discount) < 0 else (price - discount)

                if coupon['distype'] == 2:
                    disprice = round(price * coupon['discount'] / 100)

            freight = 1000 if item_type == 2 and price < 9900 else 0
            fee = disprice + freight
            result.update({'fee': fee, 'freight': freight})
            # if paytype == 2:  # 支付宝支付
            #     alipay_info = ALIPAY_CONF['order_info'].format(orderno=order_no,
            #                                                    title=title,
            #                                                    body='有菜订单',
            #                                                    price=fee / 100,
            #                                                    apptype=APPTYPE_YOUCAI,
            #                                                    extra=coupon_id if coupon_id else '')
            #     sign = base64.encodebytes(rsa.sign(alipay_info.encode(), PRI_KEY, 'SHA-1')).decode().replace('\n', '')
            #     alipay = alipay_info + ('&sign="%s"&sign_type="RSA"' % urllib.parse.quote_plus(sign))
            #     result.update({'alipay': alipay})
            # elif paytype == 3:  # 微信支付
            #     params = {
            #         'appid': YOUCAI_WXPAY_CONF['appid'],
            #         'mch_id': YOUCAI_WXPAY_CONF['mchid'],
            #         'nonce_str': uuid.uuid4().hex,
            #         'body': title,
            #         'detail': '有菜订单',
            #         'attach': coupon_id if coupon_id else '',
            #         'out_trade_no': order_no,
            #         'total_fee': fee,
            #         'spbill_create_ip': self.request.remote_ip,
            #         'notify_url': YOUCAI_WXPAY_CONF['notify'],
            #         'trade_type': 'APP'
            #     }
            #     params.update({'sign': wxpay_sign(params)})
            #     try:
            #         xml = xmltodict.unparse({'xml': params}, full_document=False)
            #         resp = yield AsyncHTTPClient().fetch(YOUCAI_WXPAY_CONF['url'] + '/pay/unifiedorder', method='POST',
            #                                              body=xml)
            #         ret = xmltodict.parse(resp.body.decode())['xml']
            #         if ret['return_code'] == 'SUCCESS' and ret['result_code'] == 'SUCCESS':
            #             sign = ret.pop('sign')
            #             if sign == wxpay_sign(ret):
            #                 pay_params = {
            #                     'appid': YOUCAI_WXPAY_CONF['appid'],
            #                     'partnerid': YOUCAI_WXPAY_CONF['mchid'],
            #                     'prepayid': ret['prepay_id'],
            #                     'package': 'Sign=WXPay',
            #                     'noncestr': uuid.uuid4().hex,
            #                     'timestamp': round(time.time())
            #                 }
            #                 pay_params.update({'sign': wxpay_sign(pay_params)})
            #                 pay_params.pop('appid')
            #                 result.update({'wxpay': pay_params})
            #     except Exception as e:
            #         log.error(e)

        return self.write(result)

    def get_seckill_item(self, uid, item_id):
        query = {'uid': uid, 'siid': item_id}
        try:
            return self.db[_DATABASE].user_seckill.find_one(query)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def add_seckill_item(self, uid, item_id):
        now = round(time.time() * 1000)
        try:
            return self.db[_DATABASE].user_seckill.insert({
                'id': mongo_uid(_DATABASE, 'user_seckill'),
                "uid": uid,
                "siid": item_id,
                'created': now
            })
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_combo_info(self, combo_id):
        # Get combo info
        query = {'id': combo_id}
        filters = {'_id': 0, 'created': 0, 'modified': 0}

        try:
            return self.db[_DATABASE].combo.find_one(query, filters)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_order(self, uid, order_type=1):
        query = {'uid': uid, 'type': order_type}
        filters = {'_id': 0, 'combo_idx': 1, 'times': 1, 'created': 1}
        try:
            return self.db[_DATABASE].order.find_one(query, filters)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_order_info(self, uid, combo_id):
        query = {'uid': uid, 'combo_id': combo_id, 'status': {'$in': [1, 2, 3]}}
        filters = {'_id': 0, 'times': 1, 'created': 1, 'combo_idx': 1, 'chgtime': 1}
        sort = [("id", -1)]

        try:
            return self.db[_DATABASE].order.find(query, filters).sort(sort).to_list(None)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_combo_order(self, uid, combo_id, order_type=1):
        query = {'uid': uid, 'combo_id': combo_id, 'type': order_type}
        filters = {'_id': 0}
        try:
            return self.db[_DATABASE].order.find_one(query, filters)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_previous_order(self, uid):
        query = {'uid': uid, 'type': {'$in': [1, 2, 4]}}
        filters = {'_id': 0, 'orderno': 1, 'combo_id': 1, 'combo_idx': 1, 'name': 1, 'mobile': 1, 'address': 1}
        sort = [("id", -1)]

        try:
            return self.db[_DATABASE].order.find(query, filters).sort(sort).limit(1).to_list(1)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_previous_items(self, order_no):
        query = {'orderno': order_no}
        filters = {"_id": 0, 'title': 1, 'img': 1, 'packw': 1, 'packs': 1}

        try:
            return self.db[_DATABASE].order_item.find(query, filters).to_list(None)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    @staticmethod
    def get_combo_price(combo, combo_idx):
        prices = combo['prices']
        if not isinstance(prices, list) or not prices:
            log.error("combo prices error")
            return 0
        try:
            return prices[combo_idx]
        except IndexError:
            log.error("price: combo_idx out of range")
            raise

    @staticmethod
    def validate_items(items_list):
        for item in items_list:
            match = re.match(r"^(\d+)\:(\d+)$", item)
            if not match:
                return False
        return True

    def get_item(self, item_id):
        query = {'id': item_id}
        filters = {'_id': 0,
                   'title': 1,
                   'imgs': 1,
                   'packw': 1}
        sort = [('id', -1)]
        try:
            return self.db[_DATABASE].issue_item.find(query, filters).sort(sort).limit(1).to_list(1)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_recom_item(self, item_id):
        query = {'id': item_id}
        filters = {'_id': 0,
                   'title': 1,
                   'imgs': 1,
                   'packw': 1,
                   'type': 1}
        sort = [('id', -1)]
        try:
            return self.db[_DATABASE].recom_item.find(query, filters).sort(sort).limit(1).to_list(1)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_item_price(self, item_id):
        query = {'id': item_id}
        filters = {'_id': 0,
                   'price': 1,
                   'title': 1,
                   'img': 1}
        sort = [('id', -1)]
        try:
            return self.db[_DATABASE].item.find(query, filters).sort(sort).limit(1).to_list(1)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def get_recom_price(self, item_id):
        query = {'id': item_id}
        filters = {'_id': 0,
                   'price': 1,
                   'title': 1,
                   'img': 1}
        sort = [('id', -1)]
        try:
            return self.db[_DATABASE].recom_item.find(query, filters).sort(sort).limit(1).to_list(1)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def create_order(self, oid, order_no, combo_order_no, order_type, item_type, price, status, times,
                     combo, combo_idx, name, mobile, address, memo, title=None):
        oid = oid
        order_no = order_no
        combo_order_no = combo_order_no
        order_type = order_type  # 1 for combo order
        item_type = item_type
        uid = self.userid
        combo_idx = combo_idx
        if not combo:
            combo_id = None
            title = title
            img = ''
            year = None
            issue_no = None
        else:
            combo_id = combo['id']
            title = combo['title']
            img = combo['img']
            year = combo['year']
            issue_no = combo['issue_no']
        price = price
        times = times
        name = name
        mobile = mobile
        address = address
        paytype = 0
        status = status  # 0 means haven't payed yet

        now = round(time.time() * 1000)
        if order_type == 2:
            chgtime = {"0": now, "1": now}
        else:
            chgtime = {"0": now}

        kwargs = dict(id=oid, orderno=order_no, con=combo_order_no, uid=uid,
                      combo_id=combo_id, combo_idx=combo_idx, coupon_id=0,
                      title=title, img=img, year=year, issue_no=issue_no, type=order_type, item_type=item_type,
                      price=price, times=times, name=name, mobile=mobile, address=address, memo=memo,
                      paytype=paytype, status=status, chgtime=chgtime, created=now, modified=now)

        try:
            return self.db[_DATABASE].order.insert(kwargs)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    def insert_items(self, items_list):

        try:
            return self.db[_DATABASE].order_item.insert(items_list)
        except Exception as exc:
            log.error(exc)
            return self.write(error(ErrorCode.DBERR))

    @coroutine
    def add_extras(self, order_no, items_list):
        items = []
        for raw_item in items_list:
            match = re.match(r"^(\d+)\:(\d+)$", raw_item)
            item_id, item_amount = int(match.group(1)), int(match.group(2))
            item_obj = yield self.get_recom_item(item_id)
            if not item_obj:
                raise ItemNotFoundError(item_id)

            item_obj = item_obj[0]

            title = item_obj['title']
            try:
                img = item_obj['imgs'].pop()
            except IndexError:
                img = ''
            packw = item_obj['packw']
            packs = item_amount
            oid = mongo_uid(_DATABASE, 'order_item')
            order_no = order_no
            now = round(time.time() * 1000)

            item = {'id': oid,
                    'orderno': order_no,
                    'siid': item_id,
                    'title': title,
                    'img': img,
                    'packw': packw,
                    'packs': packs,
                    'created': now,
                    'modified': now
                    }

            items.append(item)

        yield self.insert_items(items)

    @coroutine
    def add_items(self, order_no, items_list):
        items = []
        for raw_item in items_list:
            match = re.match(r"^(\d+)\:(\d+)$", raw_item)
            item_id, item_amount = int(match.group(1)), int(match.group(2))
            item_obj = yield self.get_item(item_id)
            if not item_obj:
                raise ItemNotFoundError(item_id)

            item_obj = item_obj[0]

            title = item_obj['title']
            try:
                img = item_obj['imgs'].pop()
            except IndexError:
                img = ''
            packw = item_obj['packw']
            packs = item_amount
            oid = mongo_uid(_DATABASE, 'order_item')
            order_no = order_no
            now = round(time.time() * 1000)

            item = {'id': oid,
                    'orderno': order_no,
                    'siid': item_id,
                    'title': title,
                    'img': img,
                    'packw': packw,
                    'packs': packs,
                    'created': now,
                    'modified': now
                    }

            items.append(item)
            yield self.db[_DATABASE].issue_item.find_and_modify({'id': item_id},
                                                                {'$inc': {'sales': packs, 'remains': -packs * packw}})
        yield self.insert_items(items)

    @coroutine
    def get_extras_price(self, extra_items_list):
        price = 0
        for item in extra_items_list:
            match = re.match(r"^(\d+)\:(\d+)$", item)
            item_id, item_amount = int(match.group(1)), int(match.group(2))
            item_obj = yield self.get_recom_price(item_id)
            if not item_obj:
                raise ItemNotFoundError(item_id)
            item_obj = item_obj[0]
            item_price = item_obj['price'] * item_amount
            price += item_price

        return price

    @coroutine
    def get_extras_title(self, extra_items_list):
        title = ''
        for item in extra_items_list:
            match = re.match(r"^(\d+)\:(\d+)$", item)
            item_id, item_amount = int(match.group(1)), int(match.group(2))
            item_obj = yield self.get_recom_item(item_id)
            if not item_obj:
                continue
            item_obj = item_obj[0]
            title = item_obj['title']
            if not title:
                continue
            break

        return title
