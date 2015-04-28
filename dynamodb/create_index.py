#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2015 by Halfmoon Labs
    :license: MIT, see LICENSE for more details.
"""

#credentials in ~/.boto
#from config import AWS_ACCESS_KEY, AWS_ACCESS_KEY_SECRET

import boto.dynamodb2

from boto.dynamodb2.table import Table
nmc_blocks = Table('nmc_blocks')
nmc_tx = Table('nmc_tx')

# -----------------------------------
if __name__ == '__main__':

    import boto.dynamodb2

    from boto.dynamodb2.table import Table
   
    nmc_blocks = Table('nmc_blocks')
    nmc_tx = Table('nmc_tx')

    '''
    entry = {}


    entry['block_height'] = 1
    entry['block_hash'] = '4tdvsv4t34t34'
    entry['block_data'] = {"tx":"treter"}

    print namecoin_blocks.put_item(entry)
    #print namecoin_blocks
    '''

    reply = namecoin_blocks.get_item(block_height=1,block_hash=None)

    print reply['block_data']
