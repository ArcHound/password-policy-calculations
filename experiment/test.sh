#!/bin/bash

hashcat -a3 -m0 4char_md5_plain.txt  '?a?a?a?a' -O --show
hashcat -a3 -m0 8char_md5_plain.txt  '?a?a?a?a?a?a?1a1' -O --show
