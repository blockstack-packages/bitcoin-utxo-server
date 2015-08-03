# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2015 by Blockstack.org
    :license: MIT, see LICENSE for more details.
"""

from pprint import pprint
from pymongo import MongoClient

con = MongoClient()
db = con['bitcoin']
transactions = db.transactions


if __name__ == '__main__':

    for tx in transactions.find():
        pprint(tx)
        print '-' * 5
