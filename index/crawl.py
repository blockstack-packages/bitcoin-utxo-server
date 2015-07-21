# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2015 by Blockstack.org
    :license: MIT, see LICENSE for more details.
"""

import json
import decimal
from pymongo import MongoClient

from pybitcoin.rpc import BitcoindClient

from config import BITCOIND_SERVER, BITCOIND_PORT
from config import BITCOIND_USER, BITCOIND_PASSWD
from config import BITCOIND_USE_HTTPS
from config import FIRST_BLOCK_MAINNET

bitcoind = BitcoindClient(BITCOIND_SERVER, BITCOIND_PORT,
                         BITCOIND_USER, BITCOIND_PASSWD,
                         BITCOIND_USE_HTTPS)

con = MongoClient()
db = con['bitcoin']
transactions = db.transactions


def get_tx(bitcoind, tx_hash):
    # lookup the raw tx using the tx hash
    try:
        tx = bitcoind.getrawtransaction(tx_hash, 1)
    except:
        return None
    return tx


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


def save_to_mongo(transaction, block_num, tx_hash):
    transaction = json.loads(json.dumps(transaction, default=decimal_default))  #to fix Decimal is not JSON serializable
    data = {}
    data['block'] = block_num
    data['tx_hash'] = tx_hash
    data['transaction'] = transaction
    transactions.insert(data)


def process_transaction(tx_hash, block_num):

    data = get_tx(bitcoind, tx_hash)
    if data is None:
        return

    if 'vout' in data:
        outputs = data['vout']
        for output in outputs:
            output_script = output['scriptPubKey']

            output_type = output_script.get('type')
            output_asm = output_script.get('asm')

            if output_asm[0:9] == 'OP_RETURN' and output_type == "nulldata":
                print "Saving OP_RETURN transaction"
                save_to_mongo(data, block_num, tx_hash)


def process_block(block_num):

    block_hash = bitcoind.getblockhash(block_num)
    block_data = bitcoind.getblock(block_hash)

    if 'tx' in block_data:
        tx_hashes = block_data['tx']
        print "Found %d transactions" % len(tx_hashes)
        for tx_hash in tx_hashes:
            #print "Transaction ID: " + tx_hash
            process_transaction(tx_hash, block_num)
        print "# ----------------------------"

if __name__ == '__main__':
    start_block_num, end_block_num = FIRST_BLOCK_MAINNET, bitcoind.getblockcount()
    #start_block_num, end_block_num = 364899, 364899

    for block_num in range(start_block_num, end_block_num + 1):
        print "Procesing block %d" % block_num
        process_block(block_num)
