#!/usr/bin/env python
# Bitcoin private key importer
# Copyright (C) 2011 by Matt Giuca
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

# Instructions:
#   Requirements: bitcointools in the Python path.
#				   Commit d3a1daf (Feb 24, 2011) or later is required.
#				   Don't ask me why Git version IDs are so hard to compare!
#				 Bitcoin version 0.3.20 (for -rescan).
#   Recommended:  A version of pycrypto in the Python path which supports
#				   RIPEMD160 hashing (not the Debian/Ubuntu version).
#				 The program 'priv_der' compiled in the current directory
#				   (required if supplying a small 32-byte key).
#   1. Get the private key you wish to import in a text file (this file can
#	  contain whitespace or newlines, and be in base-58 or base-64).
#	  Alternatively, it can be a binary file.
#	  This can be either a small 32-byte private key, or a full 279-byte DER
#	  key (including the private key). Note that 'priv_der' must be compiled
#	  if a small key is supplied.
#   2. Run privkeyimport.py KEYFILE. This will write the key into your Bitcoin
#	  wallet. Use -n to just print without writing to the wallet.
#	  Use --base64 if the input is base-64, -b if it is binary.
#   3. Run bitcoin -rescan to ensure any transactions belonging to the
#	  imported key are added to the transaction list and balance.

import sys
import optparse
import re
import binascii
import subprocess
import bsddb.db

# BitcoinTools
#from bitcointools import util
#from bitcointools import wallet
#from bitcointools import base58
import util
import wallet
import base58

def getTextLines(text):
	'Get the all the lines of text of a text.'
	textLines = text.replace('\r', '\n').replace('\n\n', '\n').split('\n')
	if len(textLines) == 1:
		if textLines[0] == '':
			return []
	return textLines

def privkey_b58_bin(priv_b58):
	"""Convert a base-58 private key (ignoring whitespace) into a binary
	string."""
	# Cut out whitespace
	priv_b58 = re.sub("[ \t\n]", "", priv_b58)
	if len(priv_b58) == 381:
		return base58.b58decode(priv_b58, 279)
	elif len(priv_b58) == 44:
		return base58.b58decode(priv_b58, 32)
	else:
		raise ValueError("Expected a key of 44 or 381 base-58 digits")

def privkey_b64_bin(priv_b64):
	"""Convert a base-64 private key (ignoring whitespace) into a binary
	string."""
	# Cut out whitespace
	priv_b64 = re.sub("[ \t\n]", "", priv_b64)
	if len(priv_b64) in (44, 372):
		return binascii.a2b_base64(priv_b64)
	else:
		raise ValueError("Expected a key of 44 or 372 base-64 digits")

def priv_to_der(priv):
	"""Convert a small 32-byte private key into a full 279-byte DER key
	(including the public key).
	This requires that priv_der has been compiled.
	priv must be a binary string of 32 bytes.
	"""
	p = subprocess.Popen(['./priv_der'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	stdout, stderr = p.communicate(priv)
	return stdout

def import_key(keyLine, db_dir, input_mode="b58", dryrun=False,verbose=False):
	if len(keyLine.strip()) == 0:
		return
	if input_mode == "b58":
		priv_bin = privkey_b58_bin(keyLine)
	elif input_mode == "b64":
		priv_bin = privkey_b64_bin(keyLine)
	elif input_mode == "bin":
		if len(keyLine) not in (32, 279):
			raise ValueError("Expected a key of 32 or 279 bytes")
		priv_bin = keyLine

	if len(priv_bin) == 32:
		# Get the full DER key
		priv_bin = priv_to_der(priv_bin)

	# The public key of a DER-encoded private key is just the last 65 bytes
	pub_bin = priv_bin[-65:]

	# Print out the key and address
	if verbose:
		print "Private key: %s" % util.long_hex(priv_bin)
		print "Public key:  %s" % util.long_hex(pub_bin)
	else:
		print "Private key: %s" % util.short_hex(priv_bin)
		print "Public key:  %s" % util.short_hex(pub_bin)
	addr = base58.public_key_to_bc_address(pub_bin)
	if addr == '':
		# This can happen if pycrypto is not installed, or if the RIPEMD160
		# hash is not available (it has been removed in the Debian/Ubuntu
		# version)
		print "Warning: Cannot calculate address; check pycrypto library"
	else:
		print "Address:	 %s" % addr

	# Data for wallet.update_wallet
	data = {
		'private_key': priv_bin,
		'public_key': pub_bin,
	}

	try:
		db_env = util.create_env(db_dir)
	except bsddb.db.DBNoSuchFileError:
		logging.error("Couldn't open " + db_dir)
		sys.exit(1)

	if not dryrun:
		db = wallet.open_wallet(db_env, writable=True)
		wallet.update_wallet(db, 'key', data)
		db.close()

def main(args=None):
	# Usage message without all of the options
	usage = """%prog [OPTIONS] KEYFILE
	Import a private key into your Bitcoin wallet.
	The private key must be a full 279-byte DER key. By default, it must be in
	base58 notation (and may have whitespace). This may be changed to base64
	or binary input."""

	if args is None:
		args = sys.argv[1:]

	# Parse arguments and options
	parser = optparse.OptionParser(usage)
	parser.add_option("-n", "--dry-run",
		action="store_true", dest="dryrun", default=False,
		help="don't actually write to the wallet")
	parser.add_option("-v", "--verbose",
		action="store_true", dest="verbose", default=False,
		help="print out the full public/private keys")
	parser.add_option("--datadir",
		action="store", dest="datadir", default=None,
		help="look for files here (defaults to bitcoin default)")
	parser.add_option("-b", "--binary",
		action="store_true", dest="input_bin", default=False,
		help="input file is binary (not base58)")
	parser.add_option("--base64",
		action="store_true", dest="input_b64", default=False,
		help="input file is base64 (not base58)")

	(options, args) = parser.parse_args(args)

	if options.input_bin and options.input_b64:
		parser.error("Can't specify both --binary and --base64.")
	elif options.input_bin:
		input_mode = "bin"
	elif options.input_b64:
		input_mode = "b64"
	else:
		input_mode = "b58"

	if len(args) >= 1:
		keyfile = open(args[0], 'rb' if options.input_bin else 'r')
	else:
		keyfile = sys.stdin

	if options.datadir is None:
		db_dir = util.determine_db_dir()
	else:
		db_dir = options.datadir

	for keyLine in getTextLines(keyfile.read()):
		import_key(keyLine, db_dir, input_mode=input_mode, dryrun=options.dryrun, verbose=options.verbose)

if __name__ == "__main__":
	sys.exit(main())
