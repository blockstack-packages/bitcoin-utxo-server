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

mongo_blocks.ensure_index('block_num')
mongo_tx.ensure_index('tx_hash')
mongo_utxo.ensure_index('id')
mongo_inputs.ensure_index('id')
mongo_address_utxo.ensure_index('address')
mongo_address_to_keys.ensure_index('address')


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
def add_utxo_to_address(output):

    id = output['id']
    output = output['data']

    output_value = output['value']

    recipient_address = get_address_from_output(output)

    #if this address appears for the first time, add a new object in mongodb;
    #else update it
    if output_value is not None and recipient_address is not None:
        exist = mongo_address_utxo.find_one({'address': recipient_address})

        if exist is None:
            entry = {}
            entry['address'] = recipient_address
            utxos = []
            utxos.append(id)
            entry['utxos'] = utxos
            mongo_address_utxo.insert(entry)
        else:
            entry = exist
            if id not in entry['utxos']:
                entry['utxos'].append(id)
            mongo_address_utxo.save(entry)


# -----------------------------------
def spend_utxo(id):

    input = mongo_inputs.find({"id": id}).limit(1)

    print "processing: " + id

    if input is not None:

        output = mongo_utxo.find_one({"id": id})
        if output is not None and 'data' in output:
                recipient_address = get_address_from_output(output['data'])

        else:
                print "no data in output: " + str(id)
                print output
                recipient_address = None

        entry = mongo_address_utxo.find_one({"address": recipient_address})
        try:
            entry['utxos'].remove(output['id'])
            mongo_address_utxo.save(entry)
        except:
            print id + " not in address index"

        print "Spending UTXO: " + id
        mongo_utxo.remove({"id": id})
    else:
        print "UTXO still unspent: " + str(id)
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
                    add_utxo_to_address(new_output)


# -----------------------------------
def process_blocks_from_beginning():

    #start_block_num, end_block_num = 1, namecoind.getblockcount()
    start_block_num, end_block_num = 1, 228718

    for block_num in range(start_block_num, end_block_num + 1):
        #save_block(block_num)
        process_block(block_num)


# -----------------------------------
def check_all_utxo():

    for utxo in mongo_utxo.find():

        spend_utxo(utxo['id'])


# -----------------------------------
def get_unspents(address):

    reply = {}
    reply['unspent_outputs'] = []

    entry = mongo_address_utxo.find_one({"address": address})

    if entry is not None:
        for id in entry['utxos']:
            new_entry = {}
            new_entry['txid'] = id.rsplit('_')[0]
            new_entry['vout'] = id.rsplit('_')[1]
            utxo = mongo_utxo.find_one({'id': id})

            new_entry['scriptPubKey'] = utxo['data']['scriptPubKey']
            new_entry['amount'] = utxo['data']['value']
            reply['unspent_outputs'].append(new_entry)

    return reply


# -----------------------------------
def create_address_to_keys_index():

    reply = namecoind.name_filter('u/')

    for user in reply:

        key = user['name']
        data = namecoind.name_show(user['name'])

        owner_address = data['address']

        print key
        print owner_address
        print '-' * 5

        exist = mongo_address_to_keys.find_one({'address': owner_address})

        if exist is None:
            entry = {}
            entry['address'] = owner_address
            keys = []
            keys.append(user['name'])
            entry['keys'] = keys
            mongo_address_to_keys.insert(entry)
        else:
            entry = exist
            if key not in entry['keys']:
                entry['keys'].append(key)
            mongo_address_to_keys.save(entry)


# -----------------------------------
if __name__ == '__main__':

    #process_blocks_from_beginning()
    #check_all_utxo()
    #write_unspents()
    #check_all_utxo()

    #pprint(get_unspents('N6xwxpamTpbKn3QA8PfttVB9rRkKkHBcZy'))

    #create_address_to_keys_index()
    check_all_utxo()