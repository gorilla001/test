# -*- coding: utf-8 -*-
import os
from multiprocessing import cpu_count
from util.logger import initlog

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log = initlog({
    'INFO': '%s/log/youcai-web.info.log' % ROOT_PATH,
    'NOTE': '%s/log/youcai-web.note.log' % ROOT_PATH,
    'WARN': '%s/log/youcai-web.warn.log' % ROOT_PATH,
    'ERROR': '%s/log/youcai-web.error.log' % ROOT_PATH
}, True, mode='timed', backup_count=15)

CACHE_SERVER = {'host': '192.168.1.100', 'port': 6379, 'db': 4, 'password': 'redis%sqc'}
SESSION_SERVER = {'host': '192.168.1.100', 'port': 6379, 'db': 0, 'password': 'redis%sqc'}
MONGO_HAMLET = {'master': '192.168.1.100:27017'}
MONGO_STORE = {'master': '192.168.1.100:27017'}
MONGO_UTIL = {'master': '192.168.1.100:27017'}
MONGO_YOUCAI = {'master': '192.168.1.100:27017'}

BASE36_NUMERALS = 'HAMLET502CZY81SQBU3FVOI4KWNJ6PXGR79D'
BASE62_NUMERALS = 'wGnSbEdvzL6K7JkVUOj1RDFhYm0IxNu2Hp94gtAo8X3yqlBcMZaCQesrWfTiP5'
SESSION_SECRET = 'L97GIeMeRDOknl36WjbRnM2LQwsg5UNsqNUBCERvDJs='
SESSION_TIMEOUT = 7200

ALIPAY_CONF = {
    'mapi_url': 'https://mapi.alipay.com/gateway.do?',
    'partner': '2088911366083289',
    'public_key': b'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnxj/9qwVfgoUh/y2W89L6BkRAFljhNhgPdyPuBV64bfQNN1PjbCzkIM6qRdKBoLPXmKKMiFYnkd6rAoprih3/PrQEB/VsW8OoM8fxn67UDYuyBTqA23MML9q1+ilIZwBC2AQ2UBVOrFXfFl75p6/B5KsiNG9zpgmLCUYuLkxpLQIDAQAB',
    'private_key': b'MIICXQIBAAKBgQDjLlvyd2O7P81Etnz8yfX4+5pxLSh+UlQWPrtNRZoMIOd/BCn2N84SO33UNJKel8f7mANGS41nmV15jRhVj8IuwCpQsYbwumlpiFlibyAKokiQ2UQNDlwwPxTXwCehIqFZoCotUIXiVXL0XbcgpVOi9jnRy3XPGAtL2nC3iofklQIDAQABAoGAaMbu3Us3EhuA/pnz11sGOQlB18TuEiTCZ2gTVrYtMD7Uxf4TpF1ki4AoroB4xvBV6bHYgMlDtG5FcFQkzwF4mtySjvpmUvD9Kf51jW/7kiv4W7SzYoq7Yr/0pl04eKP6lGSBfhnOJVRtghCpWl1Ay4GxOH5t+5aNDkx+lQGTOJkCQQD8eF19sDihJd7c0jOFYbGeYEx4l1HgjweNV2FUG5h2BdHccDo4Zx2rBgNgja+rI5RC6Ke+XexshMog1ut4tby7AkEA5lt62/tUfGPru+l27Mi2jn+JH9KhWIoNASfNpHJughAvvXFk+0ECZ1tSELKSPY+9XzVdndm4C/znT/YaMPP27wJBAI5zk7zBW5KBfbf22p8dukx0ZXF9X/NmgIpdjUsZrvKY4gqRQChm9jRzViB6kW3sy1DdWRhugmHQowPYgFBBqtUCQDVidfKNKGM7dOIzlNADI+uaOtkZIzM1qxXdd5bovht+TNIGeXSQ+FGjpD0iZSnHKgfqgiuWzURZ8/FgA2nc4BkCQQCyqQZdTT0DLntebflYYOYygtbGFYVvRv4rC+obHX+wIi5g8jDMdObYuZPXtwrfLJqEh9jVTRsjQYocbB8pzoI7'
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
IMAGE_DOMAIN = '/static/upload'
UPLOAD_PATH = os.path.join(ROOT_PATH, 'static', 'upload')
UPLOAD_DOC_PATH = os.path.join(ROOT_PATH, 'static', 'upload', 'import')
IMG_CACHE_URL = 'http://7xjgn9.com2.z0.glb.qiniucdn.com'

YC_USER_LIST_STORE_PATH = '/tmp'
YC_USER_DOWNLOAD_URL = '/api/static_file'

CPU_COUNT = cpu_count()

SMS_SERVER = {
    'hosts': [{'addr': ('192.168.1.100', 5200), 'timeout': 2000}],
    'thrift': os.path.join(ROOT_PATH, 'conf', 'smserver.thrift'),
}

GRAVATAR_URL = 'https://secure.gravatar.com/avatar/{hash}?s=160&d=identicon'
