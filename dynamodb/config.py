# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2015 by Halfmoon Labs
    :license: MIT, see LICENSE for more details.
"""

import os

try:
    AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
    AWS_ACCESS_KEY_SECRET = os.environ['AWS_ACCESS_KEY_SECRET']
except:
    print "AWS credentials not found"
    AWS_ACCESS_KEY = AWS_ACCESS_KEY_SECRET = None
