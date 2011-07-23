#!/bin/sh
#
# Script to open the bash terminal in this directory.
#
# Usage: set the executable property to true if it isn't already.  Then double click the file.
#
echo 'Directory listing:'
echo ''
ls
echo ''
echo 'To run a python script (.py) listed above, try typing something like:'
echo 'python filename'
echo ''
echo 'For example, in the bitcointools directory you could run dbdump.py --wallet by typing:'
echo 'python dbdump.py --wallet'
echo ''
bash

