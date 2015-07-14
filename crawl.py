import json
import decimal
from bitcoinrpc.authproxy import AuthServiceProxy
from pymongo import Connection
from config import *

authproxy_config_uri = '%s://%s:%s@%s:%s' % (BITCOIND_PROTOCOL, BITCOIND_USER, BITCOIND_PASSWD, BITCOIND_SERVER, BITCOIND_PORT)
bitcoind = AuthServiceProxy(authproxy_config_uri)

con = Connection()
db = con['bitcoin']
transactions = db.transactions

#-----------------------------------------
def get_tx(bitcoind, tx_hash):
    # lookup the raw tx using the tx hash
    try:
        tx = bitcoind.getrawtransaction(tx_hash, 1)
    except:
        return None
    return tx

#-----------------------------------------
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

#-----------------------------------------
def save_to_mongo(data):
	data = json.loads(json.dumps(data, default=decimal_default))  #to fix Decimal is not JSON serializable
	transactions.insert(data)

#-----------------------------------------
def process_transaction(tx_hash):
	
	# tx_hash = '2077f4b64dcbd86e655724f5308093f84722b667ad3c3a9264a3fab538fbca30'
	data = get_tx(bitcoind, tx_hash)
	if data is None:
		return

	if 'vout' in data:
		outputs = data['vout']
		for output in outputs:
			output_script = output['scriptPubKey']
	        output_type = output_script.get('type')
	        output_asm = output_script.get('asm')
	        output_hex = output_script.get('hex')
	        output_addresses = output_script.get('addresses')
	       	
	        if output_asm[0:9] == 'OP_RETURN' and output_hex:
	        	print "Saving OP_RETURN transaction to mongodb"
	    		save_to_mongo(data)

#-----------------------------------------
def process_block(block_num):
	
	# block_hash = bitcoind.getblockhash(364899)
	block_hash = bitcoind.getblockhash(block_num)
	block_data = bitcoind.getblock(block_hash)

	if 'tx' in block_data:
		tx_hashes = block_data['tx']
		print "Found %d transactions" % len(tx_hashes)
		for tx_hash in tx_hashes:
			print "Transaction ID: " + tx_hash
			process_transaction(tx_hash)
			print "# ----------------------------"
			break
		print "\n\n"

#-----------------------------------------
start_block_num, end_block_num = 1, bitcoind.getblockcount()
# start_block_num, end_block_num = 364899, 364899 

for block_num in range(start_block_num, end_block_num + 1):
    print "Procesing block %d" % block_num
    process_block(block_num)

   