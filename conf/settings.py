# -*- coding: utf-8 -*-
import os
from multiprocessing import cpu_count
from util.logger import initlog

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY_PATH = os.path.dirname(ROOT_PATH)
PROCESS_SN = os.path.basename(ROOT_PATH)
log = initlog({
    'INFO': '%s/log/estate-portal-%s.info.log' % (DEPLOY_PATH, PROCESS_SN),
    'NOTE': '%s/log/estate-portal-%s.note.log' % (DEPLOY_PATH, PROCESS_SN),
    'ERROR': '%s/log/estate-portal-%s.error.log' % (DEPLOY_PATH, PROCESS_SN)
}, mode='timed', backup_count=15)

CACHE_SERVER = {'host': '127.0.0.1', 'port': 9736, 'db': 1, 'password': 'h4M1eT#S0z'}
SESSION_SERVER = {'host': '127.0.0.1', 'port': 9736, 'db': 4, 'password': 'h4M1eT#S0z'}
MONGO_HAMLET = {'master': 'mongodb://sqc_user:zY#s9C)1z0@127.0.0.1:28017/hamlet', 'slave': 'mongodb://sqc_read:)Z!0c(S3yZ@127.0.0.1:28017/hamlet', 'replset': 'sqc'}
MONGO_STORE = {'master': 'mongodb://sqc_user:zY#s9C)1z0@127.0.0.1:28017/store', 'slave': 'mongodb://sqc_read:)Z!0c(S3yZ@127.0.0.1:28017/store', 'replset': 'sqc'}
MONGO_UTIL = {'master': 'mongodb://sqc_user:zY#s9C)1z0@127.0.0.1:28017/util', 'slave': 'mongodb://sqc_read:)Z!0c(S3yZ@127.0.0.1:28017/util', 'replset': 'sqc'}
MONGO_YOUCAI = {'master': 'mongodb://sqc_user:zY#s9C)1z0@127.0.0.1:28017/youcai', 'slave': 'mongodb://sqc_read:)Z!0c(S3yZ@127.0.0.1:28017/youcai', 'replset': 'sqc'}

BASE36_NUMERALS = 'HAMLET502CZY81SQBU3FVOI4KWNJ6PXGR79D'
BASE62_NUMERALS = 'wGnSbEdvzL6K7JkVUOj1RDFhYm0IxNu2Hp94gtAo8X3yqlBcMZaCQesrWfTiP5'
SESSION_SECRET = 'L97GIeMeRDOknl36WjbRnM2LQwsg5UNsqNUBCERvDJs='
SESSION_TIMEOUT = 7200

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
