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

from time import sleep

# ------------------------------------

from config import INDEX_DB_URI

db = MongoClient(INDEX_DB_URI)['namecoin_index']
blocks_index = db.blocks
tx_index = db.tx

#outputs are a superset of utxo (unspent outputs)
utxo_index = db.utxo
inputs_index = db.inputs
address_to_utxo = db.address_to_utxo
address_to_keys = db.address_to_keys

blocks_index.ensure_index('block_num')
tx_index.ensure_index('tx_hash')
utxo_index.ensure_index('id')
inputs_index.ensure_index('id')
address_to_utxo.ensure_index('address')
address_to_utxo.ensure_index('utxo')
address_to_keys.ensure_index('address')


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

    check_input = inputs_index.find({"id": id}).limit(1)

    if check_input.count() != 0:
        print "already spent: " + str(id)
        return

    check_entry = address_to_utxo.find({"utxo": id}).limit(1)

    if check_entry.count() != 0:
        print "already in index: " + str(id)
        return

    output = output['data']

    output_value = output['value']

    recipient_address = get_address_from_output(output)

    if output_value is not None and recipient_address is not None:

        entry = {}

        entry['utxo'] = id
        entry['address'] = recipient_address
        address_to_utxo.insert(entry)
        #print entry


# -----------------------------------
def spend_utxo(id):

    check_input = inputs_index.find({"id": id}).limit(1)

    if check_input.count() == 0:
        #print "UTXO still unspent: " + str(id)
        pass
    else:

        utxo = utxo_index.find_one({"id": id})

        if utxo is not None:
            print "Spending UTXO: " + str(id)
            utxo_index.remove({"id": id})

        entry = address_to_utxo.find_one({"utxo": id})

        if entry is not None:
            print "Spending UTXO (address index): " + str(id)
            address_to_utxo.remove({"utxo": id})


# -----------------------------------
def save_block(block_num):

    check_block = blocks_index.find({"block_num": block_num}).limit(1)

    if check_block.count() != 0:
        print "Block already in index"
        return

    #print "Saving block %d" % block_num
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
                    #inputs_index.insert(new_input)

                else:
                    print "input already in index: " + id

                spend_utxo(id)


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

                    print "inserting utxo: " + id
                    #utxo_index.insert(new_output)
                else:
                    #pass
                    print "utxo already in index: " + id
            else:
                #pass
                print "utxo already spent: " + id


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

            process_input(tx_data)
            process_output(tx_data, tx_hash)


# -----------------------------------
def process_blocks(start_block, end_block):

    #start_block_num, end_block_num = 1, namecoind.getblockcount()
    #start_block_num, end_block_num = 228718, 231714

    for block_num in range(start_block, end_block + 1):
        print "Processing block: ", block_num
        #save_block(block_num)
        #process_block(block_num)


# -----------------------------------
def process_new_block(block_num):
    print "Processing block: ", block_num
    #save_block(block_num)
    #process_block(block_num)


# -----------------------------------
def check_all_utxo():

    counter = 0

    for utxo in utxo_index.find():

        spend_utxo(utxo['id'])
        counter += 1

        if counter % 100 == 0:
            print counter


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

        #if counter == 100:
        #    exit(0)

        add_utxo_to_address(utxo)


# -----------------------------------
def get_unspents(address):

    reply = {}
    reply['unspent_outputs'] = []

    for entry in address_to_utxo.find({"address": address}):

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
def sync_with_blockchain(old_block):

    new_block = namecoind.blocks()

    print "last processed block: %s" % old_block

    while(1):

        while(old_block == new_block):
            sleep(30)
            new_block = namecoind.blocks()

        print 'current block: %s' % new_block

        for block_num in range(old_block + 1, new_block + 1):
            process_new_block(block_num)

        old_block = new_block

# -----------------------------------
if __name__ == '__main__':

    #process_blocks(0,100)
    #check_all_utxo()
    #create_address_to_keys_index()
    #create_address_to_utxo_index()
    #exit(0)

    #process_new_block(228722)

    sync_with_blockchain(231893)

    '''
    print "utxo:\t", utxo_index.find().count()
    print "inputs:\t", inputs_index.find().count()
    print "tx:\t", tx_index.find().count()
    '''

    '''
    address = 'NBSffD6N6sABDxNooLZxL26jwGetiFHN6H'

    from pprint import pprint
    info = get_unspents(address)
    sum = 0
    for i in info['unspent_outputs']:
        sum += i['amount']

    print sum

    exit(0)
    '''