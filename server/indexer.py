# -*- coding: utf-8 -*-
"""
    :copyright: (c) 2015 by Blockstack.org
    :license: MIT, see LICENSE for more details.
"""

import json
from flask import Flask, jsonify
from bson import json_util, ObjectId
from pymongo import MongoClient

app = Flask(__name__)

con = MongoClient()
db = con['bitcoin']
transactions = db.transactions


@app.route("/")
def index():
    return "Welcome to home page!"


@app.route("/blocks/<block_num>")
def get_block(block_num):

    block_num = int(block_num)
    items = transactions.find({'block': block_num})

    if items.count() == 0:
        return "No OP_RETURN transactions found for the given block"

    transaction = []
    for item in items:
        item = json.loads(json_util.dumps(item))
        transaction.append(item['tx_hash'])

    return jsonify({'transactions': transaction})


@app.route("/tx/<tx_hash>")
def get_transaction(tx_hash):

    tx = transactions.find_one({'tx_hash': tx_hash})

    if tx is None:
        return "Transaction not in index of OP_RETURN transactions"

    return jsonify({'transaction': tx['transaction']})


if __name__ == '__main__':
    app.run(debug=True)
