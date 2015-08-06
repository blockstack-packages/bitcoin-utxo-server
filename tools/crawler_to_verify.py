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

from urllib import urlopen, urlretrieve
from lxml.html import parse
from lxml.cssselect import CSSSelector
from pymongo import Connection

# ------------------------------------
BASE_URL = 'http://bkchain.org/nmc/address/'
con = Connection()
db = con['namecoin_unspents']
mongo_unspents = db.unspents2

# ------------------------------------

count = 0, success_count = 0, failed_count = 0
for item in mongo_unspents.find():
    count += 1
    address = item['address']
    amount = item['value']
    url = BASE_URL + address

    print "Comparing address: %s" % address
    page = parse(urlopen(url)).getroot()
    selector = CSSSelector("table tbody tr td")
    dom = selector(page)

    balance = float(dom[1].text.split(" ")[0])
    print "balance from our code is %f" % amount
    print "balance from bkchain is %f" % balance
    if balance == amount:
        print "Matched!\n"
        success_count += 1
    else:
        print "Doesn't Match!\n"
        failed_count += 1

    if count == 1000:
        break

print "Compared %d address: %d success, %d failures" % (count, success_count, failed_count)
