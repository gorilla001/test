# -*- coding: utf-8 -*-
import os
from multiprocessing import cpu_count
from util.logger import initlog

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log = initlog({
    'INFO': '%s/log/estate-portal.info.log' % ROOT_PATH,
    'NOTE': '%s/log/estate-portal.note.log' % ROOT_PATH,
    'WARN': '%s/log/estate-portal.warn.log' % ROOT_PATH,
    'ERROR': '%s/log/estate-portal.error.log' % ROOT_PATH
}, True, mode='timed', backup_count=15)

CACHE_SERVER = {'host': '192.168.1.100', 'port': 6379, 'db': 1, 'password': 'redis%sqc'}
SESSION_SERVER = {'host': '192.168.1.100', 'port': 6379, 'db': 4, 'password': 'redis%sqc'}
MONGO_HAMLET = {'master': '192.168.1.100:27017'}
MONGO_STORE = {'master': '192.168.1.100:27017'}
MONGO_UTIL = {'master': '192.168.1.100:27017'}
MONGO_YOUCAI = {'master': '192.168.1.100:27017'}

BASE36_NUMERALS = 'HAMLET502CZY81SQBU3FVOI4KWNJ6PXGR79D'
BASE62_NUMERALS = 'wGnSbEdvzL6K7JkVUOj1RDFhYm0IxNu2Hp94gtAo8X3yqlBcMZaCQesrWfTiP5'
SESSION_SECRET = 'L97GIeMeRDOknl36WjbRnM2LQwsg5UNsqNUBCERvDJs='
SESSION_TIMEOUT = 7200

IMAGE_DEFAULT = 'https://img.shequcun.com/zone.jpg'
IMAGE_DOMAIN = '/static/upload'
UPLOAD_PATH = os.path.join(ROOT_PATH, 'static', 'upload')
UPLOAD_DOC_PATH = os.path.join(ROOT_PATH, 'static', 'upload', 'import')
IMG_CACHE_URL = 'http://7xjgn9.com2.z0.glb.qiniucdn.com'

YC_USER_LIST_STORE_PATH = '/tmp'
YC_USER_DOWNLOAD_URL = '/api/static_file'

CPU_COUNT = cpu_count()

SMS_SERVER = {
    'hosts': [{'addr': ('192.168.1.100', 5200), 'timeout': 2000}, {'addr': ('192.168.1.100', 5201), 'timeout': 2000}],
    'thrift': os.path.join(ROOT_PATH, 'conf', 'smserver.thrift'),
}

GRAVATAR_URL = 'https://secure.gravatar.com/avatar/{hash}?s=160&d=identicon'
