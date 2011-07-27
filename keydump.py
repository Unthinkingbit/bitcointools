#!/usr/bin/env python
#
# Code for dumping the bitcoin Berkeley db keys in a human-readable format
#
from base58 import b58encode, public_key_to_bc_address, bc_address_to_hash_160, hash_160
from BCDataStream import *
from bsddb.db import *
import cStringIO
import logging
import sys
from util import determine_db_dir, create_env, short_hex, long_hex


def dump_keys(db_env, addressStart, outputFileName):
	db = DB(db_env)
	try:
		r = db.open("wallet.dat", "main", DB_BTREE, DB_THREAD|DB_RDONLY)
	except DBError:
		logging.error("Couldn't open addr.dat/main. Try quitting Bitcoin and running this again.")
		return

	cString = cStringIO.StringIO()
	kds = BCDataStream()
	vds = BCDataStream()

	for (key, value) in db.items():
		kds.clear(); kds.write(key)
		vds.clear(); vds.write(value)
		type = kds.read_string()
		if type == "key":
			publicKey = kds.read_bytes(kds.read_compact_size())
			privateKey = vds.read_bytes(vds.read_compact_size())
			address = public_key_to_bc_address(publicKey)
			if address.startswith(addressStart):
				privateKey58 = b58encode(privateKey)
				cString.write('%s\n' % privateKey58)
				print("\nPubKey hex: "+ long_hex(publicKey) + "\nPubKey base58: "+ b58encode(publicKey) + "\nAddress: " +
					address + "\nPriKey hex: "+ long_hex(privateKey) + "\nPriKey base58: "+ privateKey58 + "\n")

	outputText = cString.getvalue()
	if outputText != '':
		writeFileText(outputFileName, outputText)

	db.close()

def writeFileText(fileName, fileText, writeMode='w+'):
	'Write a text to a file.'
	try:
		file = open(fileName, writeMode)
		file.write(fileText)
		file.close()
	except IOError:
		print('The file ' + fileName + ' can not be written to.')


def main():
	import optparse
	parser = optparse.OptionParser(usage="%prog [options]")
	parser.add_option("--datadir", dest="datadir", default=None, help="Look for files here (defaults to bitcoin default)")
	parser.add_option("--address", action="store", dest="addressStart", default="", help="Print keys in the wallet.dat file")
	parser.add_option("--out", action="store", dest="outputFileName", default="key.txt", help="Save keys in wallet.dat to output file name")
	(options, args) = parser.parse_args()

	if options.datadir is None:
		db_dir = determine_db_dir()
	else:
		db_dir = options.datadir

	try:
		db_env = create_env(db_dir)
	except DBNoSuchFileError:
		logging.error("Couldn't open " + db_dir)
		sys.exit(1)

	dump_keys(db_env, options.addressStart, options.outputFileName)
	db_env.close()

if __name__ == '__main__':
    main()
