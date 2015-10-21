# -*- coding: utf-8 -*-

import re
import rsa
import time
import uuid
import base64
import xmltodict
import hashlib
from urllib.parse import urlencode
from constants import APPTYPE_YOUCAI_H5
from operator import itemgetter
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient
from conf.settings import log, WXPAY_CONF, ALIPAY_CONF
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

def wxpay_sign(params):
    query = []
    for param in sorted(params.items(), key=itemgetter(0)):
        if param[1]:
            query.append('%s=%s' % (param[0], param[1]))

    query.append('key=' + YOUCAI_WXPAY_CONF['key'])
    return hashlib.md5('&'.join(query).encode()).hexdigest().upper()

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
            raw_extras = self.get_argument('extras', None)  # 格式：id1:amount1,id2:amount2...
            name = self.get_argument('name')
            mobile = self.get_argument('mobile')
            address = self.get_argument('address')
            memo = self.get_argument('memo', '')
            paytype = int(self.get_argument('paytype', None) or 2)
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.PARAMERR))

        if not name or not mobile or not address:
            log.error("name or mobile or address must specified")
            return self.write(error(ErrorCode.PARAMERR))

        if not raw_extras:
            log.error("raw extras can't be null")
            return self.write(error(ErrorCode.PARAMERR))

        oid = mongo_uid(_DATABASE, 'order')
        order_no = gen_orderno(oid, short=True)  # used for alipay also
        # combo_order_no = 0
        order_type = 3
        status = 0
        times = 0
        item_type = 2
        fid = 0
        fname = ''

        # farm_and_items = {}
        raw_extras_list = raw_extras.split(',')
        for item in raw_extras_list:                             # 这里其实还残留有问题，暂时只是购买一件商品还可以，要是
            match = re.match(r"^(\d+)\:(\d+)$", item)           # 多件商品，而且商品列表中已经有一件购买过的秒杀商品 -->
            item_id = int(match.group(1))                        # 中途报错，会使用户不能购买一些自己没有购买过的秒杀品
            item_obj = yield self.get_recom_item(item_id)
            if not item_obj:
                raise ItemNotFoundError(item_id)

            item_obj = item_obj[0]
            recom_type = item_obj['type']

            if not fid:     # 既然不存在拆分订单，只要fid和fname赋过值，就无需再赋值
                fid = item_obj['fid']
            if not fname:
                fname = item_obj['farm']

            if recom_type == 2:  # 秒杀  然后只需对秒杀品特殊处理，删除普通单品无用处理
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
        combo_order_no = 0

        # freight
        freight = 1000 if item_type == 2 and price < 9900 else 0

        yield self.create_order(oid, order_no, combo_order_no, order_type, item_type, price, freight, status,
                                times, fid, fname, combo, combo_idx, name, mobile, address, memo, title)

        try:
            yield self.add_extras(order_no, raw_extras_list)
        except ItemNotFoundError as exc:
            log.error(exc)
            return self.write(error(ErrorCode.NODATA, '要购买的菜品在数据库找不到'))

        result = {'orderno': str(order_no)}

        fee = price + freight
        result.update({'fee': fee, 'freight': freight})
        if paytype == 2:  # 支付宝支付
            alipay_info = {
                'partner': "2088911366083289",
                'seller_id': "2088911366083289",
                'out_trade_no': order_no,
                'subject': title,
                'body': "有菜H5订单",
                'total_fee': "%.2f" % (fee/100),
                'notify_url': "https://api.shequcun.com/alipay/notify?apptype={apptype}".format(apptype=APPTYPE_YOUCAI_H5),
                'service': "alipay.wap.create.direct.pay.by.user",
                'payment_type': "1",
                '_input_charset': "utf-8",
                'it_b_pay': "30m",
                'return_url': "https://youcai.shequcun.com/#!/pay_result"
            }
            acc = []
            for param in sorted(alipay_info.items(), key=itemgetter(0)):
                if param[1]:
                    acc.append('%s=%s' % (param[0], param[1]))

            sign = base64.encodebytes(rsa.sign('&'.join(acc).encode(), PRI_KEY, 'SHA-1')).decode().replace('\n', '')
            alipay_info.update({
                'sign': sign,
                'sign_type': 'RSA'
            })
            resp = yield AsyncHTTPClient().fetch("https://mapi.alipay.com/gateway.do?" + urlencode(alipay_info))
            # result.update({'alipay': "https://mapi.alipay.com/gateway.do?" + urlencode(alipay_info)})
            result.update({'alipay': resp.effective_url})
        elif paytype == 3:  # 微信支付
            params = {
                'appid': YOUCAI_WXPAY_CONF['appid'],
                'mch_id': YOUCAI_WXPAY_CONF['mchid'],
                'nonce_str': uuid.uuid4().hex,
                'body': title,
                'detail': '公众号扫码订单',
                'out_trade_no': order_no,
                'total_fee': fee,
                'spbill_create_ip': self.request.remote_ip,
                'notify_url': YOUCAI_WXPAY_CONF['notify'],
                'trade_type': 'JSAPI',
                'openid': self.session.get('openid')
            }
            params.update({'sign': wxpay_sign(params)})
            try:
                xml = xmltodict.unparse({'xml': params}, full_document=False)
                resp = yield AsyncHTTPClient().fetch(YOUCAI_WXPAY_CONF['url'] + '/pay/unifiedorder', method='POST', body=xml)
                ret = xmltodict.parse(resp.body.decode())['xml']

                if ret['return_code'] == 'SUCCESS' and ret['result_code'] == 'SUCCESS':
                    sign = ret.pop('sign')
                    if sign == wxpay_sign(ret):
                        pay_params = {
                            'appId': YOUCAI_WXPAY_CONF['appid'],
                            'timeStamp': round(time.time()),
                            'nonceStr': uuid.uuid4().hex,
                            'package': 'prepay_id={prepay_id}'.format(prepay_id=ret['prepay_id']),
                            'signType': 'MD5'
                        }
                        ret_sign = wxpay_sign(pay_params)
                        pay_params.update({'paySign': ret_sign})

                        self.session['wx_pay'] = pay_params
                        self.session.save()
                else:
                    log.error(ret)
            except Exception as e:
                log.error(e)

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

    def get_recom_item(self, item_id):
        query = {'id': item_id}
        filters = {'_id': 0,
                   'title': 1,
                   'imgs': 1,
                   'packw': 1,
                   'type': 1,
                   'fid': 1,
                   'farm': 1}
        sort = [('id', -1)]
        try:
            return self.db[_DATABASE].recom_item.find(query, filters).sort(sort).limit(1).to_list(1)
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

    def create_order(self, oid, order_no, combo_order_no, order_type, item_type, price, freight, status, times, fid, farm,
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
        freight = freight
        times = times
        name = name
        mobile = mobile
        address = address
        paytype = 0
        status = status  # 0 means haven't payed yet
        fid = fid
        farm = farm

        now = round(time.time() * 1000)
        if order_type == 2:
            chgtime = {"0": now, "1": now}
        else:
            chgtime = {"0": now}

        kwargs = dict(id=oid, orderno=order_no, con=combo_order_no, uid=uid,
                      combo_id=combo_id, combo_idx=combo_idx, coupon_id=0, fid=fid, farm=farm,
                      title=title, img=img, year=year, issue_no=issue_no, type=order_type, item_type=item_type,
                      price=price, freight=freight, times=times, name=name, mobile=mobile, address=address, memo=memo,
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
