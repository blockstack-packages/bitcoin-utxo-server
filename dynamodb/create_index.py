#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2015 by Halfmoon Labs
    :license: MIT, see LICENSE for more details.
"""

#credentials in ~/.boto
#from config import AWS_ACCESS_KEY, AWS_ACCESS_KEY_SECRET

import boto.dynamodb2
from config import *
from coinrpc import NamecoindServer
from boto.dynamodb2.table import Table
nmc_blocks = Table('nmc_blocks')
nmc_tx = Table('nmc_tx')

# -----------------------------------
if __name__ == '__main__':

    namecoind = NamecoindServer(NAMECOIND_SERVER, NAMECOIND_PORT, NAMECOIND_USER, NAMECOIND_PASSWD, USE_HTTPS)

    start_block_num, end_block_num = 1, namecoind.getblockcount()

    error_blocks = []
    error_tx = []

    # start_block_num, end_block_num = 100000, 100050
    for block_num in range(start_block_num, end_block_num + 1):

        print "Procesing block %d" % block_num
        #block_hash = namecoind.getblockhash(block_num)
        block = namecoind.getblockbycount(block_num)

        block_entry = {}

        block_entry['block_num'] = block_num
        if 'tx' in block:
            block_entry['block_data'] = block

        #insert in DynamoDB
        try:
            nmc_blocks.put_item(block_entry)
        except:
            error_blocks.append(block_num)

        if 'tx' in block:
            txs = block['tx']
            print "Found %d transactions" % len(txs)
            for tx in txs:
                print "Transaction ID: " + tx

                raw_tx = namecoind.getrawtransaction(tx)
                tx_data = namecoind.decoderawtransaction(raw_tx)

                tx_entry = {}
                tx_entry['tx_hash'] = str(tx)
                tx_entry['tx_data'] = tx_data

                #insert in DynamoDB
        try:
                    nmc_tx.put_item(tx_entry)
        except:
                        error_tx.append(tx)

    print error_blocks
    print error_tx