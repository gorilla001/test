# -*- coding: utf-8 -*-
import uuid
import hashlib
import xmltodict
import time
from operator import itemgetter
from conf.settings import log, WXPAY_CONF
from tornado.httpclient import HTTPClient

YOUCAI_WXPAY_CONF = WXPAY_CONF['youcai']


def wxpay_sign(params):
    query = []
    for param in sorted(params.items(), key=itemgetter(0)):
        if param[1]:
            query.append('%s=%s' % (param[0], param[1]))

    query.append('key=' + YOUCAI_WXPAY_CONF['key'])
    return hashlib.md5('&'.join(query).encode()).hexdigest().upper()


def make_order(openid, title, order_no, fee, remote_ip):
    params = {
        'appid': YOUCAI_WXPAY_CONF['appid'],
        'mch_id': YOUCAI_WXPAY_CONF['mchid'],
        'nonce_str': uuid.uuid4().hex,
        'body': title,
        'detail': '公众号扫码订单',
        'attach': '',
        'out_trade_no': order_no,
        'total_fee': fee,
        'spbill_create_ip': remote_ip,
        'notify_url': YOUCAI_WXPAY_CONF['notify'],
        'trade_type': 'JSAPI',
        'openid': openid
    }
    params.update({'sign': wxpay_sign(params)})
    try:
        xml = xmltodict.unparse({'xml': params}, full_document=False)
        resp = HTTPClient().fetch(YOUCAI_WXPAY_CONF['url'] + '/pay/unifiedorder', method='POST',
                                  body=xml)
        ret = xmltodict.parse(resp.body.decode())['xml']
        pay_params = {}
        if ret['return_code'] == 'SUCCESS' and ret['result_code'] == 'SUCCESS':
            sign = ret.pop('sign')
            if sign == wxpay_sign(ret):
                pay_params = {
                    'appId': YOUCAI_WXPAY_CONF['appid'],
                    'timeStamp': round(time.time()),
                    'nonceStr': uuid.uuid4().hex,
                    'package': 'prepay_id={prepay_id}'.format(prepay_id=ret['prepay_id']),
                    'signType': 'MD5',
                    'paySign': sign
                }
        else:
            log.error(ret)

        return pay_params
    except Exception as e:
        log.error(e)
