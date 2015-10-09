# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'conf'))
sys.modules.update({"conf.settings": __import__("debug_settings")})


if __name__ == "__main__":
    from main import start
    start()