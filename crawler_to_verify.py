from urllib import urlopen, urlretrieve
from lxml.html import parse
from lxml.cssselect import CSSSelector
from pymongo import Connection

# ------------------------------------
BASE_URL = 'http://bkchain.org/nmc/address/'
con = Connection()
db = con['namecoin_unspents']
mongo_unspents = db.unspents2

# ------------------------------------

count = 0, success_count = 0, failed_count = 0
for item in mongo_unspents.find():
	count += 1
	address = item['address']
	amount = item['value']
	url = BASE_URL + address

	print "Comparing address: %s" % address
	page = parse(urlopen(url)).getroot()
	selector = CSSSelector("table tbody tr td")
	dom = selector(page)

	balance = float(dom[1].text.split(" ")[0])
	print "balance from our code is %f" % amount
	print "balance from bkchain is %f" % balance
	if balance == amount:
		print "Matched!\n"
		success_count += 1
	else:
		print "Doesn't Match!\n"
		failed_count += 1

	if count == 1000:
		break

print "Compared %d address: %d success, %d failures" % (count, success_count, failed_count)
