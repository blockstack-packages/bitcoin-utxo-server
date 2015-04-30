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

mongo_blocks.ensure_index('block_num')
mongo_tx.ensure_index('tx_hash')
mongo_utxo.ensure_index('id')
mongo_inputs.ensure_index('id')


# -----------------------------------
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


# -----------------------------------
def spend_utxo(id):

    input = mongo_inputs.find_one({"id": id})

    if input is not None:
        print "Spending UTXO: " + id
        mongo_utxo.remove({"id": id})
    else:
        print "UTXO still unspent"
        #print id


# -----------------------------------
def save_block(block_num):

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
def process_block(block_num):
    ''' Processes DB data
    '''

    print "Procesing block %d" % block_num
    block = mongo_blocks.find_one({'block_num': block_num})

    block_data = block['block_data']

    if 'tx' in block_data:
        txs = block_data['tx']

        for tx in txs:
            tx_hash = tx
            tx = mongo_tx.find_one({'tx_hash': tx_hash})

            tx_data = tx['tx_data']

            if 'vin' in tx_data:

                for input in tx_data['vin']:

                    if 'txid' in input:
                        id = input['txid'] + '_' + str(input['vout'])

                        new_input = {}

                        new_input['id'] = id
                        new_input['data'] = input

                        mongo_inputs.insert(new_input)

                        # spend the output
                        spend_utxo(id)

            if 'vout' in tx_data:

                for output in tx_data['vout']:

                    id = tx_hash + '_' + str(output['n'])

                    new_output = {}
                    new_output['id'] = id
                    new_output['data'] = output

                    mongo_utxo.insert(new_output)


# -----------------------------------
def process_blocks_from_beginning():

    #start_block_num, end_block_num = 1, namecoind.getblockcount()
    start_block_num, end_block_num = 1, 1000

    for block_num in range(start_block_num, end_block_num + 1):
        save_block(block_num)
        process_block(block_num)


# -----------------------------------
def check_all_utxo():

    for utxo in mongo_utxo.find():

        spend_utxo(utxo)

# -----------------------------------
if __name__ == '__main__':

    #process_blocks_from_beginning()
    check_all_utxo()
    #write_unspents()
    #spend_utxo()