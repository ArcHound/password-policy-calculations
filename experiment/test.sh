#!/bin/bash

# This is what I want to run on the VM

for file in $(find $1 -name "*.txt"); do
	echo $file
	date +"%T.%6N"
	# some fancy filename into command parsing
	mode=$(echo $file | cut -f2 -d'_')
	len=$(echo $file | cut -f3 -d'_' | sed 's/len//')
	charset=$(echo $file | cut -f4 -d'_' | sed 's/.txt//')
	chars=""
	case "$charset" in
		"numbers")
			chars="?d" ;;
		"lowercase")
			chars="?l" ;;
		"uppercase")
			chars="?u" ;;
		"ascii-printable")
			chars="?a" ;;
	esac
	mask=""
	for i in $( seq 1 $len); do
		mask="${mask}${chars}"
	done
	# last check
	echo $mode $file $mask
	# and run!
	hashcat --quiet -o $file.cracked -O -a 3 -m $mode "$file" "$mask" 
done;

# shuffle the output files into one big file with answers
for file in $(find $1 -name "*.cracked"); do
	cat $file >> $1/cracked_answers.log
	rm $file
done;
