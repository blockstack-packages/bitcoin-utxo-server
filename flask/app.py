import json
from flask import Flask, jsonify
from bson import json_util, ObjectId
from pymongo import Connection

app = Flask(__name__)

con = Connection()
db = con['bitcoin']
transactions = db.transactions

#-----------------------------------------
@app.route("/")
def index():
	return "Welcome to home page!"

#-----------------------------------------
@app.route("/blocks/<block_num>")
def blocks(block_num):
	
	block_num = int(block_num)
	items = transactions.find({'block': block_num})

	if items.count() == 0:
		return "No OP_RETURN transactions found for the given block"
	
	transaction = []
	for item in items:
		item = json.loads(json_util.dumps(item))
		transaction.append(item)

	return jsonify({'transactions': transaction})

#-----------------------------------------

#run the app...

if __name__ == '__main__':
    app.run(debug = True)

