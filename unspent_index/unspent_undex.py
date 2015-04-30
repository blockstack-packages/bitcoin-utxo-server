import json
import pymongo
from pymongo import Connection
from coinrpc.namecoind_server import NamecoindServer
from coinkit import *
from config import *

# ------------------------------------
con = Connection()
db = con['namecoin_unspents']
mongo_unspents = db.unspents5

# ------------------------------------
def get_recipient_address_from_tx(tx_hash, value):
    raw = namecoind.getrawtransaction(tx_hash)
    data = namecoind.decoderawtransaction(raw)

    recipient_address = ""
    if 'vout' in data:
        outputs = data['vout']
        for output in outputs:
            output_value = output.get('value')

            if value > output_value:
                continue

            if 'scriptPubKey' in output:
                scriptPubKey = output['scriptPubKey']
                if 'addresses' in scriptPubKey:
                    recipient_address = scriptPubKey['addresses'][0]
                    
    return recipient_address
# ------------------------------------

def process_transaction(tx_hash):
    raw = namecoind.getrawtransaction(tx_hash)
    data = namecoind.decoderawtransaction(raw)

    recipient_address = ""
    if 'vout' in data:
        outputs = data['vout']
        for output in outputs:
            output_value = output.get('value')

            if 'scriptPubKey' in output:
                scriptPubKey = output['scriptPubKey']
                if 'addresses' in scriptPubKey:
                    recipient_address = scriptPubKey['addresses'][0]

            #if this address appears for the first time, add a new object in mongodb;
            #else update it
            if output_value is not None and recipient_address is not None:
                exist = mongo_unspents.find_one({'address': recipient_address})
                if exist is None:
                    mongo_unspents.insert({
                            'address': recipient_address,
                            'value': float(str(output_value))
                        })
                else:
                    exist['value'] += float(str(output_value))
                    mongo_unspents.save(exist)

            recipient_address = ""

    input_address = ""
    if 'vin' in data:
        inputs = data['vin']
        for input in inputs:
            input_value = input.get('value')
    
            if 'scriptSig' in input:
                script_sig_asm = str(input['scriptSig'].get('asm'))
                script_sig_parts = script_sig_asm.split(' ')
               
                if len(script_sig_parts) > 1 and (len(script_sig_parts[-1]) == 130 
                    or len(script_sig_parts[-1]) == 66):
                    public_key_string = script_sig_parts[-1]
                    try:
                        input_address = NamecoinPublicKey(public_key_string, verify=False).address()
                    except Exception, e:
                            print str(e)
                else:
                    #lets try to find input_address from the 'previous' transaction
                    previous_tx = input.get('txid')
                   
                    if previous_tx is None:
                        print "Coinbase Transaction"
                    else:
                        print "Trying to get input address from previous tx: " + previous_tx
                        input_address = get_recipient_address_from_tx(previous_tx, input_value)
                        print "Obtained input address = " + input_address + "\n"        
    
       
            if input_value is not None and input_address != "":
        
                exist = mongo_unspents.find_one({'address': input_address})
                exist['value'] -= float(str(input_value))
                mongo_unspents.save(exist)

            input_address = ""
            
# ------------------------------------

namecoind = NamecoindServer(NAMECOIND_SERVER, NAMECOIND_PORT, NAMECOIND_USER, NAMECOIND_PASSWD, USE_HTTPS)
#namecoind = NamecoindServer('174.129.223.66','8332','opennamesystem','opennamesystem',False)

start_block_num, end_block_num = 1, namecoind.getblockcount()

# start_block_num, end_block_num = 100000, 100050
for block_num in range(start_block_num, end_block_num + 1):
    print "Procesing block %d" % block_num
    block_hash = namecoind.getblockhash(block_num)
    block = namecoind.getblock(block_hash)

    if 'tx' in block:
        txs = block['tx']
        print "Found %d transactions" % len(txs)
        for tx in txs:
            print "Transaction ID: " + tx
            process_transaction(tx)
            # print "# ----------------------------"
        print "\n\n"

V-OUT 

{
            "value" : 39.87800000,
            "n" : 0,
            "scriptPubKey" : {
                "asm" : "046adb3ef932411649bd25a0dac786ba5f9011b6d69ea8b3d8a21d2b8e6e8cc06fe97439ec208fec557a1e17c01bb149edad182fa15729e882be2493785a9e2398 OP_CHECKSIG",
                "hex" : "41046adb3ef932411649bd25a0dac786ba5f9011b6d69ea8b3d8a21d2b8e6e8cc06fe97439ec208fec557a1e17c01bb149edad182fa15729e882be2493785a9e2398ac",
                "reqSigs" : 1,
                "type" : "pubkeyhash",
                "addresses" : [
                    "NGHMJ4ZhRtuCTWPaWPxgbCv3fQb8h2gX6M"
                ]
            }
        }



V-IN 

 {
            "txid" : "bae7839e227bcdaeae152a13bb7f9c2f75b4e51c584c5cce1093488235cfb241",
            "vout" : 0,
            "scriptSig" : {
                "asm" : "3045022006327e6fb32c62b1e0aec0c4d5183df0f1919dc4e5891edf15b40e9cdce28857022100aaf10eed82e5a550edee11e9af0383d4352d2dc6058e09d3ca3cca813dfd9dcc01",
                "hex" : "483045022006327e6fb32c62b1e0aec0c4d5183df0f1919dc4e5891edf15b40e9cdce28857022100aaf10eed82e5a550edee11e9af0383d4352d2dc6058e09d3ca3cca813dfd9dcc01"
            },
            "value" : 39.87800000,
            "sequence" : 4294967295
        }