# -*- coding: utf-8 -*-

import io
import base64
import pyqrcode
from conf.settings import log
from base import AuthHandler
from util.helper import error, ErrorCode


class QrcodeHandler(AuthHandler):
    def get(self):
        try:
            url = self.get_argument('url')
        except Exception as e:
            log.error(e)
            return self.write(error(ErrorCode.PARAMERR))

        buffer = io.BytesIO()
        url = pyqrcode.create(url)
        url.png(buffer, scale=5)
        result = base64.encodebytes(buffer.getvalue()).decode().replace('\n', '')
        return self.write(result)