#!/bin/sh

cat logs/access.log | grep redir | cut -d':' -f3 | cut -d" " -f1 | cut -d"," -f2 | sort -u
