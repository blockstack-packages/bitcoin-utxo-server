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

# ------------------------------------

from config import INDEX_DB_URI

db = MongoClient(INDEX_DB_URI)['namecoin_index']
blocks_index = db.blocks
tx_index = db.tx

#outputs are a superset of utxo (unspent outputs)
utxo_index = db.utxo
inputs_index = db.inputs
address_to_utxo = db.address_to_utxo
address_to_utxo_temp = db.address_to_utxo_temp
address_to_keys = db.address_to_keys

blocks_index.ensure_index('block_num')
tx_index.ensure_index('tx_hash')
utxo_index.ensure_index('id')
inputs_index.ensure_index('id')
address_to_utxo.ensure_index('address')
address_to_utxo_temp.ensure_index('address')
address_to_keys.ensure_index('address')

import pylibmc

from config import MEMCACHED_SERVERS
mc = pylibmc.Client(MEMCACHED_SERVERS, binary=True)

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

    if output_value is not None and recipient_address is not None:

        entry = {}

        entry['utxo'] = id
        entry['address'] = recipient_address
        address_to_utxo_temp.insert(entry)

        '''
        check_address = mc.get(recipient_address)

        if check_address is None:

            #print "not found"

            utxos = []
            utxos.append(id)
          
            mc.set(recipient_address, utxos, 0)
        else:

            utxos = mc.get(recipient_address)

            utxos.append(id)
            mc.set(recipient_address, utxos, 0)
        '''

# -----------------------------------
def spend_utxo(id):

    input = inputs_index.find({"id": id}).limit(1)

    print "processing: " + id

    if input.count() != 0:

        print "UTXO should be removed"

        '''
        output = utxo_index.find_one({"id": id})
        if output is not None and 'data' in output:
            recipient_address = get_address_from_output(output['data'])
        else:
            print "no data in output: " + str(id)
            print output
            recipient_address = None

        entry = address_to_utxo.find_one({"address": recipient_address})

        try:
            entry['utxos'].remove(output['id'])
            address_to_utxo.save(entry)
        except:
            print id + " not in address index"

        print "Spending UTXO: " + id
        utxo_index.remove({"id": id})
        '''
    else:
        print "UTXO still unspent: " + str(id)


# -----------------------------------
def save_block(block_num):

    print "Procesing block %d" % block_num
    block = namecoind.getblockbycount(block_num)

    block_entry = {}

    block_entry['block_num'] = block_num
    block_entry['block_data'] = block

    block_entry = json.loads(json.dumps(block_entry, cls=DecimalEncoder))

    blocks_index.insert(block_entry)

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

            tx_index.insert(tx_entry)


# -----------------------------------
def process_input(tx_data):

    if 'vin' in tx_data:

        for input in tx_data['vin']:

            if 'txid' in input:
                id = input['txid'] + '_' + str(input['vout'])

                check_input = inputs_index.find({"id": id}).limit(1)

                if check_input.count() == 0:

                    new_input = {}
                    new_input['id'] = id

                    print "inserting input: " + id
                    inputs_index.insert(new_input)


# -----------------------------------
def process_output(tx_data, tx_hash):

    if 'vout' in tx_data:

        for output in tx_data['vout']:

            id = tx_hash + '_' + str(output['n'])

            check_input = inputs_index.find({"id": id}).limit(1)

            #if this output is not already spent
            if check_input.count() == 0:

                check_output = utxo_index.find({"id": id}).limit(1)

                if check_output.count() == 0:

                    new_output = {}
                    new_output['id'] = id
                    new_output['data'] = output

                    print "inserting output: " + id
                    utxo_index.insert(new_output)
                else:
                    print "already in index: " + id
            else:
                print "already spent: " + id


# -----------------------------------
def process_block(block_num):
    ''' Processes DB data
    '''

    print "Processing block %d" % block_num
    block = blocks_index.find_one({'block_num': block_num})

    block_data = block['block_data']

    if 'tx' in block_data:
        txs = block_data['tx']

        for tx in txs:
            tx_hash = tx
            tx = tx_index.find_one({'tx_hash': tx_hash})

            tx_data = tx['tx_data']

            #process_input(tx_data)
            process_output(tx_data, tx_hash)


# -----------------------------------
def process_blocks_from_beginning():

    #start_block_num, end_block_num = 1, namecoind.getblockcount()
    start_block_num, end_block_num = 1, 228718

    for block_num in range(start_block_num, end_block_num + 1):
        #save_block(block_num)
        process_block(block_num)


# -----------------------------------
def check_all_utxo():

    for utxo in utxo_index.find():

        spend_utxo(utxo['id'])


# -----------------------------------
def create_address_to_utxo_index():


    counter = 0

    print "creating ..."

    for utxo in utxo_index.find():

        counter += 1

        if counter % 100 == 0:
            print counter

        #if counter < skip_counter:
        #    continue

        #if counter == 1000:
        #    exit(0)

        add_utxo_to_address(utxo)

# -----------------------------------
def get_unspents(address):

    reply = {}
    reply['unspent_outputs'] = []

    for entry in address_to_utxo_temp.find({"address": address}):
        
        id = entry['utxo']

        new_entry = {}
        new_entry['txid'] = id.rsplit('_')[0]
        new_entry['vout'] = id.rsplit('_')[1]
        utxo = utxo_index.find_one({'id': id})
    
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

        exist = address_to_keys.find_one({'address': owner_address})

        if exist is None:
            entry = {}
            entry['address'] = owner_address
            keys = []
            keys.append(user['name'])
            entry['keys'] = keys
            address_to_keys.insert(entry)
        else:
            entry = exist
            if key not in entry['keys']:
                entry['keys'].append(key)
            address_to_keys.save(entry)


# -----------------------------------
if __name__ == '__main__':

    #process_blocks_from_beginning()
    check_all_utxo()
    #create_address_to_keys_index()
    
    #create_address_to_utxo_index()

    '''
    counter = 0 

    for i in address_to_utxo_temp.find():

        counter += 1

        if counter % 100 == 0:
            print counter 

        check_utxo = address_to_utxo_temp.find({'address': i['address']})

        if check_utxo.count() > 5:

            result = get_unspents(i['address'])

            print result
            print '-' * 5 

    '''