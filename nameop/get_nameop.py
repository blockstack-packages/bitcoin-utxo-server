from pymongo import Connection
from bitcoinrpc.authproxy import AuthServiceProxy
from blockstore import build
from config import *

authproxy_config_uri = '%s://%s:%s@%s:%s' % (BITCOIND_PROTOCOL, BITCOIND_USER, BITCOIND_PASSWD, BITCOIND_SERVER, BITCOIND_PORT)
bitcoind = AuthServiceProxy(authproxy_config_uri)

con = Connection()
db = con['bitcoin']
transactions = db.transactions

blocks = []
t = transactions.find({'block': {'$gt': 343000}})
for item in t:
    blocks.append(item['block'])

blocks = list(set(blocks))      # find unique block numbers

opcode_data = []
count = 0
for block in blocks:
    count += 1
    print "%d => Processing block: %d" % (count, block)
    data = build.get_nameops_in_block(bitcoind, block)
    opcode_data.append(data)

print opcode_data
