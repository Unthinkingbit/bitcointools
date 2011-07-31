This is a modification of an old version of bitcointools:
https://github.com/gavinandresen/bitcointools

which incorporates a version of Matt Giuca's privkeyimport:
https://code.launchpad.net/~mgiuca/+junk/bitcoin-import

The purpose of this bitcointools version is to export a key from a bitcoin wallet and import it into a devcoin wallet.

The procedure works, but is awkward.  Once it is possible to import and export keys from the mainline client this modification will be obsolete.

For an example of using this in Linux, quit bitcoin and make a copy of the .bitcoin directory.  Also quit devcoin and make a copy of the .devcoin directory.

Then print the bitcoin key you want to export by typing in a terminal in the bitcointools directory:
python keydump.py <the address of the key you want to export>

For example, if the address of the key you want to export is 175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W, you would type 
python keydump.py 175tWpb8K1S7NmH4Zx6rewF9WQrcZv245W

This will save the base58 version of the private key with that address to a file named key.txt.

Then in a terminal in a bitcointools directory, type:
privkeyimport.py --datadir <your home directory>/.devcoin

For example, if your home directory is david, you would type 
privkeyimport.py --datadir /home/david/.devcoin

This will add the private key with the default key file name of key.txt to the devcoin wallet.

Then run devcoin-qt -rescan by typing in a terminal in the devcoin directory:
./devcoin-qt -rescan

to ensure any transactions belonging to the imported key are added to the transaction list and balance.  Then open your devcoin-qt client and your balance will be up to date.  If the balance includes money sent to that private key, then even if you don't see your key in your receive address book, the key is in your wallet.

Once everything works, delete the file named key.txt so that if someone gets access to your computer they can't copy your private key and steal the money within.  For the same reason, delete the .bitcoin and .devcoin backups.  Then, assuming you encrypt your wallet after use so that if someone gets access to your computer they can't copy your wallet, encrypt the bitcoin wallet and the devcoin wallet.



Below is an explanation of other uses of bitcointools.

----- dbdump.py -----
Run    dbdump.py --help    for usage.  Database files are opened read-only, but
you might want to backup your Bitcoin wallet.dat file just in case.

You must quit Bitcoin before reading the transactions, blocks, or address database files.

Requires the pycrypto library from  http://www.dlitz.net/software/pycrypto/
to translate public keys into human-friendly Bitcoin addresses.

Examples:

Print out  wallet keys and transactions:
  dbdump.py --wallet --wallet-tx

Print out the "genesis block" (the very first block in the proof-of-work block chain):
  dbdump.py --block=000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f

Print out one of the transactions from my wallet:
  dbdump.py --transaction=c6e1bf883bceef0aa05113e189982055d9ba7212ddfc879798616a0d0828c98c
  dbdump.py --transaction=c6e1...c98c

Print out all 'received' transactions that aren't yet spent:
  dbdump.py --wallet-tx-filter='fromMe:False.*spent:False'

Print out all blocks involving transactions to the Bitcoin Faucet:
  dbdump.py --search-blocks=15VjRaDX9zpbA8LVnbrCAFzrVzN7ixHNsC

There's a special search term to look for non-standard transactions:
  dbdump.py --search-blocks=NONSTANDARD_CSCRIPTS

----- statistics.py -----
Scan all the transactions in the block chain and dump out a .csv file that shows transaction volume per month.

----- fixwallet.py -----
Half-baked utility that reads a wallet.dat and writes out a new wallet.dat.

Only half-baked because to be really useful I'd have to write serialize routines to re-pack data after modifying it...

----- jsonToCSV.py -----
Read JSON list-of-objects from standard input, writes CSV file to standard output.
Useful for converting bitcoind's listtransactions output to CSV that can be
imported into a spreadsheet.

