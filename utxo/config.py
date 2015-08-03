# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2015 by Halfmoon Labs
    :license: MIT, see LICENSE for more details.
"""

import os

from config_local import NAMECOIND_SERVER, NAMECOIND_PORT, NAMECOIND_USER, NAMECOIND_PASSWD, USE_HTTPS

try:
	INDEX_DB_URI = os.environ['INDEX_DB_URI']
except:
	print "Index DB credentials not found"
	INDEX_DB_URI = None