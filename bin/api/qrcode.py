# -*- coding: utf-8 -*-

import time
import qrcode
from hashlib import md5
from conf.settings import log
from base import AuthHandler
from util.helper import error, ErrorCode, mongo_uid, gen_orderno


class QrcodeHandler(AuthHandler):
    def get(self):
        try:
            url = self.get_argument('url')
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.PARAMERR))

        now = md5(url.encode()).hexdigest()
        img = qrcode.make(url)
        img.save('/tmp/{0}.png'.format(now))
        return self.write({'now': now})
