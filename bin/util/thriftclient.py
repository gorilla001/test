# -*- coding: utf-8 -*-
import logging
import re
import time
import traceback
import thriftpy
from thriftpy.rpc import client_context
from . import selector

log = logging.getLogger()


class ThriftClientError(Exception):
    pass


class ThriftClient(object):
    """This class is used for connect to ThriftServer and send sms"""
    # server - 为Selector对象，或者地址{'addr':('127.0.0.1',5000),'timeout':1000}
    def __init__(self, thrift_file, server):
        with open(thrift_file) as f:
            content = f.read()
        self.service = getattr(thriftpy.load(thrift_file), re.match('.*service +(\w+).*', content, re.DOTALL).group(1))
        self.start_time = time.time()
        self.server_selector = None
        self.server = None
        self.client = None
        self.raise_except = True  # 是否在调用时抛出异常

        if isinstance(server, dict):  # 只有一个server
            self.server = [server]
            self.server_selector = selector.Selector(self.server, 'random')
        elif isinstance(server, list):  # server列表，需要创建selector，策略为随机
            self.server = server
            self.server_selector = selector.Selector(self.server, 'random')
        else:  # 直接是selector
            self.server_selector = server
        while True:
            if self.open() == 0:
                break

    def open(self):
        start_time = time.time()
        err = ''
        self.server = self.server_selector.next()
        if not self.server:
            restore(self.server_selector, self.service)
            self.server = self.server_selector.next()
            if not self.server:
                log.error('server=%s|err=no server!', self.service.__name__)
                raise ThriftClientError

        addr = self.server['server']['addr']
        try:
            with client_context(self.service, addr[0], addr[1],
                                timeout=self.server['server']['timeout']) as client:
                client.ping()
        except Exception as e:
            err = str(e)
            log.error(traceback.format_exc())
            self.server['valid'] = False
        finally:
            end_time = time.time()
            tname = self.service.__name__
            pos = tname.rfind('.')
            if pos > 0:
                tname = tname[pos+1:]
            s = 'server=%s|func=open|addr=%s:%d/%d|time=%d' %\
                (tname, addr[0], addr[1], self.server['server']['timeout'], int((end_time - start_time) * 1000))
            if err:
                s += '|err=%s' % repr(err)
                log.info(s)

        if not err:
            return 0

        return -1

    def call(self, funcname, *args, **kwargs):
        def _call_log(ret, err=''):
            endtime = time.time()
            addr = self.server['server']['addr']
            tname = self.service.__name__
            pos = tname.rfind('.')
            if pos > 0:
                tname = tname[pos+1:]

            retstr = str(ret)
            if tname == 'Encryptor' and ret:
                retstr = str(ret.code)
            s = 'server=%s|func=%s|addr=%s:%d/%d|time=%d|args=%s|kwargs=%s' %\
                (tname, funcname, addr[0], addr[1], self.server['server']['timeout'],
                 int((endtime - starttime) * 1000000), args[1:len(args) - 1], kwargs)
            if err:
                s += '|ret=%s|err=%s' % (retstr, repr(err))
                log.warn(s)
            else:
                log.info(s)

        starttime = time.time()
        ret = None
        try:
            addr = self.server['server']['addr']
            with client_context(self.service, addr[0], addr[1],
                                timeout=self.server['server']['timeout']) as client:
                func = getattr(client, funcname)
                ret = func(*args, **kwargs)
        except Exception as e:
            _call_log(ret, str(e))
            log.error(traceback.format_exc())
            if self.raise_except:
                raise
        else:
            _call_log(ret)

        return ret

    def __getattr__(self, name):
        def _(*args, **kwargs):
            return self.call(name, *args, **kwargs)
        return _


def restore(selector, service):
    invalid = selector.not_valid()
    log.debug('invalid server:%s', invalid)
    for server in invalid:
        transport = None
        try:
            log.debug('try restore %s', server['server']['addr'])
            addr = server['server']['addr']
            with client_context(service, addr[0], addr[1],
                                timeout=server['server']['timeout']) as client:
                client.ping()
        except:
            log.error(traceback.format_exc())
            log.debug("restore fail: %s", server['server']['addr'])
            continue
        finally:
            if transport:
                transport.close()

        log.debug('restore ok %s', server['server']['addr'])
        server['valid'] = True


def thrift_call(thrift_file, server, funcname, *args, **kwargs):
    """
    Connect to TriftServer and call the `funcname` method on remote with args and kwargs.
    :param thrift_file:  thrift interface definition file's path.
    :param server:     triftserver list with multi-servers or dict with single server.
    :param funcname:   the method name which will be called on remote.
    :param args:       the tuple-like args pass to `funcname`.
    :param kwargs:     the dict-like args pass to `funcname`.
    :returns : None
    """
    client = ThriftClient(thrift_file, server)
    client.raise_except = True

    return client.call(funcname, *args, **kwargs)
