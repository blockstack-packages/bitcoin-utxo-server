# -*- coding: utf-8 -*-
"""
    Indexer
    ~~~~~

    copyright: (c) 2015 by Blockstack.org

This file is part of Indexer.

    Indexer is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Indexer is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Indexer. If not, see <http://www.gnu.org/licenses/>.
"""

import os

BITCOIND_SERVER = 'btcd.onename.com'
BITCOIND_PORT = '8332'
BITCOIND_USER = 'openname'
BITCOIND_PASSWD = 'opennamesystem'
BITCOIND_PROTOCOL = 'https'

try:
    INDEX_DB_URI = os.environ['INDEX_DB_URI']
except:
    print "Index DB credentials not found"
    INDEX_DB_URI = None
