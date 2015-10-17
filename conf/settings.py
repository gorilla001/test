# -*- coding: utf-8 -*-
import os
from multiprocessing import cpu_count
from util.logger import initlog

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY_PATH = os.path.dirname(ROOT_PATH)
PROCESS_SN = os.path.basename(ROOT_PATH)
log = initlog({
    'INFO': '%s/log/youcai-web-%s.info.log' % (DEPLOY_PATH, PROCESS_SN),
    'NOTE': '%s/log/youcai-web-%s.note.log' % (DEPLOY_PATH, PROCESS_SN),
    'ERROR': '%s/log/youcai-web-%s.error.log' % (DEPLOY_PATH, PROCESS_SN)
}, mode='timed', backup_count=15)

CACHE_SERVER = {'host': '127.0.0.1', 'port': 9736, 'db': 4, 'password': 'h4M1eT#S0z'}
SESSION_SERVER = {'host': '127.0.0.1', 'port': 9736, 'db': 0, 'password': 'h4M1eT#S0z'}
MONGO_HAMLET = {'master': 'mongodb://sqc_user:zY#s9C)1z0@127.0.0.1:28017/hamlet', 'slave': 'mongodb://sqc_read:)Z!0c(S3yZ@127.0.0.1:28017/hamlet', 'replset': 'sqc'}
MONGO_STORE = {'master': 'mongodb://sqc_user:zY#s9C)1z0@127.0.0.1:28017/store', 'slave': 'mongodb://sqc_read:)Z!0c(S3yZ@127.0.0.1:28017/store', 'replset': 'sqc'}
MONGO_UTIL = {'master': 'mongodb://sqc_user:zY#s9C)1z0@127.0.0.1:28017/util', 'slave': 'mongodb://sqc_read:)Z!0c(S3yZ@127.0.0.1:28017/util', 'replset': 'sqc'}
MONGO_YOUCAI = {'master': 'mongodb://sqc_user:zY#s9C)1z0@127.0.0.1:28017/youcai', 'slave': 'mongodb://sqc_read:)Z!0c(S3yZ@127.0.0.1:28017/youcai', 'replset': 'sqc'}

BASE36_NUMERALS = 'HAMLET502CZY81SQBU3FVOI4KWNJ6PXGR79D'
BASE62_NUMERALS = 'wGnSbEdvzL6K7JkVUOj1RDFhYm0IxNu2Hp94gtAo8X3yqlBcMZaCQesrWfTiP5'
SESSION_SECRET = 'L97GIeMeRDOknl36WjbRnM2LQwsg5UNsqNUBCERvDJs='
SESSION_TIMEOUT = 7200

ALIPAY_CONF = {
    'mapi_url': 'https://mapi.alipay.com/gateway.do?',
    'partner': '2088911366083289',
    'public_key': b'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnxj/9qwVfgoUh/y2W89L6BkRAFljhNhgPdyPuBV64bfQNN1PjbCzkIM6qRdKBoLPXmKKMiFYnkd6rAoprih3/PrQEB/VsW8OoM8fxn67UDYuyBTqA23MML9q1+ilIZwBC2AQ2UBVOrFXfFl75p6/B5KsiNG9zpgmLCUYuLkxpLQIDAQAB',
    'private_key': b'MIICXQIBAAKBgQDjLlvyd2O7P81Etnz8yfX4+5pxLSh+UlQWPrtNRZoMIOd/BCn2N84SO33UNJKel8f7mANGS41nmV15jRhVj8IuwCpQsYbwumlpiFlibyAKokiQ2UQNDlwwPxTXwCehIqFZoCotUIXiVXL0XbcgpVOi9jnRy3XPGAtL2nC3iofklQIDAQABAoGAaMbu3Us3EhuA/pnz11sGOQlB18TuEiTCZ2gTVrYtMD7Uxf4TpF1ki4AoroB4xvBV6bHYgMlDtG5FcFQkzwF4mtySjvpmUvD9Kf51jW/7kiv4W7SzYoq7Yr/0pl04eKP6lGSBfhnOJVRtghCpWl1Ay4GxOH5t+5aNDkx+lQGTOJkCQQD8eF19sDihJd7c0jOFYbGeYEx4l1HgjweNV2FUG5h2BdHccDo4Zx2rBgNgja+rI5RC6Ke+XexshMog1ut4tby7AkEA5lt62/tUfGPru+l27Mi2jn+JH9KhWIoNASfNpHJughAvvXFk+0ECZ1tSELKSPY+9XzVdndm4C/znT/YaMPP27wJBAI5zk7zBW5KBfbf22p8dukx0ZXF9X/NmgIpdjUsZrvKY4gqRQChm9jRzViB6kW3sy1DdWRhugmHQowPYgFBBqtUCQDVidfKNKGM7dOIzlNADI+uaOtkZIzM1qxXdd5bovht+TNIGeXSQ+FGjpD0iZSnHKgfqgiuWzURZ8/FgA2nc4BkCQQCyqQZdTT0DLntebflYYOYygtbGFYVvRv4rC+obHX+wIi5g8jDMdObYuZPXtwrfLJqEh9jVTRsjQYocbB8pzoI7',
    'order_info': 'partner="2088911366083289"&seller_id="liushouchang@shequcun.com"&out_trade_no="{orderno}"&subject="{title}"&body="{body}"&total_fee="{price:.2f}"&notify_url="https://api.shequcun.com/alipay/notify?apptype={apptype}&extra={extra}"&service="alipay.wap.create.direct.pay.by.user"&payment_type="1"&_input_charset="utf-8"&it_b_pay="30m"&show_url="m.alipay.com"'
}

WXPAY_CONF = {
    'youcai': {
        'appid': 'wx7614397bfac00107',
        'secret': 'fddc0cbd357acc9536df19aaa389ab82',
        'key': 'b891996f692e467790ad68a25cb8c8ed',
        'mchid': '1273891701',
        'url': 'https://api.mch.weixin.qq.com',
        'notify': 'https://api.shequcun.com/wxpay/notify'
    }
}

IMAGE_DEFAULT = 'https://img.shequcun.com/zone.jpg'
IMAGE_DOMAIN = 'https://img.shequcun.com'
UPLOAD_PATH = '/home/hamlet/shequcun/upload'
UPLOAD_DOC_PATH = '/home/hamlet/shequcun/upload/import'
IMG_CACHE_URL = 'http://7xjgn9.com2.z0.glb.qiniucdn.com'

YC_USER_LIST_STORE_PATH = '/home/hamlet/shequcun/upload/export'
YC_USER_DOWNLOAD_URL = 'https://img.shequcun.com/export'

CPU_COUNT = cpu_count()

SMS_SERVER = {
    'hosts': [{'addr': ('127.0.0.1', 5200), 'timeout': 2000}, {'addr': ('127.0.0.1', 5201), 'timeout': 2000}],
    'thrift': os.path.join(ROOT_PATH, 'conf', 'smserver.thrift'),
}

GRAVATAR_URL = 'https://secure.gravatar.com/avatar/{hash}?s=160&d=identicon'
