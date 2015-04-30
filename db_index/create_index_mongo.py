#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2015 by Halfmoon Labs
    :license: MIT, see LICENSE for more details.
"""

from coinrpc import NamecoindServer
import json
import decimal

from config import NAMECOIND_SERVER, NAMECOIND_PORT, NAMECOIND_USER, NAMECOIND_PASSWD, USE_HTTPS

namecoind = NamecoindServer(NAMECOIND_SERVER, NAMECOIND_PORT, NAMECOIND_USER, NAMECOIND_PASSWD, USE_HTTPS)

from pprint import pprint

from commontools import pretty_print

from pymongo import MongoClient
c = MongoClient()

# ------------------------------------
db = c['namecoin_index']
mongo_blocks = db.blocks
mongo_tx = db.tx

mongo_blocks.ensure_index('block_num')
mongo_tx.ensure_index('tx_hash')


# -----------------------------------
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


# -----------------------------------
def write_blocks_and_tx():

    start_block_num, end_block_num = 1, namecoind.getblockcount()

    error_blocks = []
    error_tx = []

    start_block_num, end_block_num = 1, 100
    for block_num in range(start_block_num, end_block_num + 1):

        print "Procesing block %d" % block_num
        block = namecoind.getblockbycount(block_num)

        block_entry = {}

        block_entry['block_num'] = block_num
        block_entry['block_data'] = block

        block_entry = json.loads(json.dumps(block_entry, cls=DecimalEncoder))

        mongo_blocks.insert(block_entry)

        if 'tx' in block:
            txs = block['tx']
            #print "Found %d transactions" % len(txs)
            for tx in txs:
                #print "Transaction ID: " + tx

                raw_tx = namecoind.getrawtransaction(tx)
                tx_data = namecoind.decoderawtransaction(raw_tx)

                tx_entry = {}
                tx_entry['tx_hash'] = str(tx)
                tx_entry['tx_data'] = tx_data

                tx_entry = json.loads(json.dumps(tx_entry, cls=DecimalEncoder))

                mongo_tx.insert(tx_entry)

# -----------------------------------
if __name__ == '__main__':

    write_blocks_and_tx()
