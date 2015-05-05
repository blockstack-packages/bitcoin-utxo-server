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

#outputs are a superset of utxo (unspent outputs)
mongo_utxo = db.utxo
mongo_inputs = db.inputs
mongo_address_utxo = db.address_utxo
mongo_address_to_keys = db.address_to_keys


# -----------------------------------
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


# -----------------------------------
def get_address_from_output(output):

    recipient_address = None

    if 'scriptPubKey' in output:
        scriptPubKey = output['scriptPubKey']

        if 'addresses' in scriptPubKey:
            recipient_address = scriptPubKey['addresses'][0]

    return recipient_address


# -----------------------------------
def test_blocks(start_block_num, end_block_num):

    for block_num in range(start_block_num, end_block_num + 1):

        if mongo_blocks.find({"block_num": block_num}).limit(1) is not None:
            print "check: " + str(block_num)
        else:
            print "error: " + str(block_num)
            exit(0)


# -----------------------------------
def test_index_data():

    start_block_num, end_block_num = 220000, 228718

    #test_blocks(start_block_num, end_block_num)

    for block_num in range(start_block_num, end_block_num + 1):

        block = mongo_blocks.find_one({"block_num": block_num})

        block_data = block['block_data']

        print "processing: " + str(block_num)

        if block_data is not None:
            if 'tx' in block_data:
                for tx in block_data['tx']:
                    tx_hash = tx
                    check_tx = mongo_tx.find_one({'tx_hash': tx_hash})
                    tx_data = check_tx['tx_data']

                    if 'vout' in tx_data:

                        for output in tx_data['vout']:

                            id = tx_hash + '_' + str(output['n'])

                            check_spent = mongo_inputs.find({"id": id}).limit(1)

                            if check_spent is None:
                                print "found unspent: " + id
                            
        else:
            print "error: empty block" + str(block_num)
            exit(0)


# -----------------------------------
if __name__ == '__main__':

    test_index_data()