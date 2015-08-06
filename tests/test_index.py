#!/usr/bin/env python
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
blocks_index = db.blocks
tx_index = db.tx

#outputs are a superset of utxo (unspent outputs)
utxo_index = db.utxo
inputs_index = db.inputs
address_to_utxo = db.address_to_utxo
address_to_keys = db.address_to_keys


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

        if blocks_index.find({"block_num": block_num}).limit(1).count() == 1:
            print "check: " + str(block_num)
        else:
            print "error: " + str(block_num)
            exit(0)


# -----------------------------------
def test_index_data():

    start_block_num, end_block_num = 220000, 228718

    #test_blocks(start_block_num, end_block_num)

    for block_num in range(start_block_num, end_block_num + 1):

        block = blocks_index.find_one({"block_num": block_num})

        block_data = block['block_data']

        print "processing: " + str(block_num)

        if block_data is not None:
            if 'tx' in block_data:
                for tx in block_data['tx']:
                    tx_hash = tx
                    check_tx = tx_index.find_one({'tx_hash': tx_hash})
                    tx_data = check_tx['tx_data']

                    if 'vout' in tx_data:

                        for output in tx_data['vout']:

                            id = tx_hash + '_' + str(output['n'])

                            check_input = inputs_index.find({"id": id}).limit(1)

                            if check_input.count() == 0:
                                print "found unspent: " + id

        else:
            print "error: empty block" + str(block_num)
            exit(0)


# -----------------------------------
if __name__ == '__main__':

    test_index_data()