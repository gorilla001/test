# -*- coding: utf-8 -*-
import datetime
import decimal
import hashlib
import json
import os
import random
import struct
import time
import pymongo
from conf.settings import BASE36_NUMERALS, BASE62_NUMERALS, MONGO_UTIL
from util.mongotool import MongoProxy

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
conn_util = pymongo.MongoClient(MONGO_UTIL['master'])
json.encoder.c_make_encoder = None
json.encoder.FLOAT_REPR = lambda v: str(int(v)) if v.is_integer() else str(v)


class ErrorCode(object):
    DBERR = 1000
    IOERR = 1001
    SRVERR = 1002
    THIRDERR = 1003
    PARAMERR = 2000
    LOGINERR = 2001
    PWDERR = 2002
    USERERR = 2003
    ROLEERR = 2004
    REQERR = 3000
    IPLIMIT = 3001
    DATAERR = 3002
    CODEERR = 3100
    CODEXPIRE = 3101
    NODATA = 4000
    DATAEXIST = 4001
    NOUSER = 4002
    USEREXIST = 4003
    UNKOWN = 5000

error_message = {
    ErrorCode.DBERR: '数据库查询错误',
    ErrorCode.IOERR: '文件读写错误',
    ErrorCode.SRVERR: '内部服务错误',
    ErrorCode.THIRDERR: '外部服务错误',
    ErrorCode.PARAMERR: '参数错误',
    ErrorCode.LOGINERR: '用户未登录',
    ErrorCode.PWDERR: '密码错误',
    ErrorCode.USERERR: '用户状态异常',
    ErrorCode.ROLEERR: '用户身份错误',
    ErrorCode.REQERR: '请求数据错误',
    ErrorCode.IPLIMIT: 'IP受限',
    ErrorCode.DATAERR: '数据错误',
    ErrorCode.CODEERR: '验证码错误',
    ErrorCode.CODEXPIRE: '验证码已过期',
    ErrorCode.NODATA: '数据不存在',
    ErrorCode.DATAEXIST: '数据已存在',
    ErrorCode.NOUSER: '用户不存在',
    ErrorCode.USEREXIST: '用户已存在',
    ErrorCode.UNKOWN: '未知错误'
}


# 文件头标志位
ext_flag = {
    'FFD8FF': '.jpg',
    '89504E47': '.png',
    '47494638': '.gif',
    '49492A00': '.tif',
    '424D': '.bmp',
    '41433130': '.dwg',
    '38425053': '.psd',
    '7B5C727466': '.rtf',
    '3C3F786D6C': '.xml',
    '68746D6C3E': '.html',
    '44656C69766572792D646174653A': '.eml',
    'CFAD12FEC5FD746F': '.dbx',
    '2142444E': '.pst',
    'D0CF11E0': '.xlsdoc',
    '5374616E64617264204A': '.mdb',
    'FF575043': '.wpd',
    '252150532D41646F6265': '.epsps',
    '255044462D312E': '.pdf',
    'AC9EBD8F': '.qdf',
    'E3828596': '.pwl',
    '504B0304': '.zip',
    '52617221': '.rar',
    '57415645': '.wav',
    '41564920': '.avi',
    '2E7261FD': '.ram',
    '2E524D46': '.rm',
    '000001BA': '.mpg',
    '000001B3': '.mpg',
    '6D6F6F76': '.mov',
    '3026B2758E66CF11': '.asf',
    '4D546864': '.mid'
}


def __hexdigest(algorithm, salt, raw_password):
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)

    if algorithm == 'md5':
        return hashlib.md5(salt.encode() + raw_password.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt.encode() + raw_password.encode()).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")


def __constant_time_compare(val1, val2):
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0


def check_password(raw_password, enc_password):
    if enc_password:
        parts = enc_password.split('$')
        if len(parts) == 3:
            algo, salt, hsh = parts
            return __constant_time_compare(hsh, __hexdigest(algo, salt, raw_password))

    return False


def gen_password(raw_password):
    if raw_password is None:
        return '!'
    else:
        import random

        algo = 'sha1'
        salt = __hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = __hexdigest(algo, salt, raw_password)
        return '%s$%s$%s' % (algo, salt, hsh)


def singleton(cls, *args, **kwargs):
    instances = {}

    def get_instance():
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


# 增强型json编码器
class ExtendedEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            if type(o) == decimal.Decimal:
                v = float(o)
                return int(v) if v.is_integer() else v
            elif type(o) == datetime.date:
                return o.strftime(DATE_FORMAT)
            elif type(o) == datetime.datetime:
                return o.strftime(DATETIME_FORMAT)
            elif type(o) == datetime.time:
                return o.strftime(TIME_FORMAT)
            elif type(o) == datetime.timedelta:
                minute, second = divmod(o.seconds, 60)
                hour, minute = divmod(minute, 60)
                return datetime.time(hour, minute, second).strftime(TIME_FORMAT)
            else:
                return json.JSONEncoder.default(self, o)
        except:
            return str(o)


def json_dumps(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    except:
        return str(obj)


def error(errcode, errmsg=''):
    return {'errcode': errcode, "errmsg": errmsg if errmsg else error_message[errcode]}


def mongo_uid(dbname, colname, uid=None):
    """
    返回mongodb集合的自增id
    :param dbname: 数据库名
    :param colname: 集合名
    :param uid: None - 返回自增id, int值 - 设置当前id
    :return: 当前id
    """
    coll = MongoProxy(conn_util).util.sequence
    now = round(time.time() * 1000)
    if uid:
        update = {'$set': {'seq': uid, 'modified': now}}
    else:
        update = {'$inc': {'seq': 1}, '$set': {'modified': now}}

    ret = coll.find_and_modify({'dbname': dbname, 'colname': colname}, update, new=True, fields={'_id': 0, 'seq': 1})
    return ret['seq']


# 字节码转16进制字符串
def bytes2hex(bytes):
    num = len(bytes)
    hexstr = ''

    for i in range(num):
        t = '%x' % bytes[i]
        if len(t) % 2:
            hexstr += '0'
        hexstr += t
    return hexstr.upper()


# 获取文件类型
def __filetype(src, type='file'):
    if type == 'file' and (not os.path.isfile(src) or os.path.getsize(src) < 14) or len(src) < 14:
        return None

    ftype = 'UNKNOWN'
    if type == 'file':
        fp = open(src, 'rb')
        head = fp.read(14)
        fp.close()
    else:
        head = src[:14]

    for hcode in ext_flag.keys():
        numOfBytes = len(hcode) // 2
        hbytes = struct.unpack_from('B' * numOfBytes, head[:numOfBytes])  # 'B'表示一个字节
        f_hcode = bytes2hex(hbytes)
        if f_hcode == hcode:
            ftype = ext_flag[hcode]
            break

    return ftype


def filetype(filename):
    return __filetype(filename, 'file')


def streamtype(stream):
    return __filetype(stream, 'stream')


def baseconvert(num, numerals=BASE36_NUMERALS):
    if num == 0:
        return numerals[0]

    if num < 0:
        sign = '-'
        num = -num
    else:
        sign = ''

    base = len(numerals)
    result = ''
    while num:
        result = numerals[num % base] + result
        num //= base

    return sign + result


def coupon_code():
    seed = str(round(time.time() * 1000))
    box = [seed[-(i+1)] for i in range(len(seed))]
    box[0], box[-1] = box[-1], box[0]
    for i in (3, 6, 12):
        box.insert(i, str(random.randint(0, 9)))

    return baseconvert(int(''.join(box)) ^ 882375596620796, BASE62_NUMERALS)


def gen_orderno(pid, short=False):
    src = '%09d%s' % (pid, time.strftime('%m%y', time.localtime()))
    box = [src[-(i+1)] for i in range(len(src))]
    box[0], box[1] = box[1], box[0]
    if short:
        for i in (3, 6, 10):
            box.insert(i, str(random.randint(0, 9)))
        return int(''.join(box)) ^ 11010515011926
    else:
        for i in (3, 6, 7, 15, 17):
            box.insert(i, str(random.randint(0, 9)))
        return int(''.join(box)) ^ 1101052015011915
