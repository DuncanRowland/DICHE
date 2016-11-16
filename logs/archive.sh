#!/bin/bash -e

cd /home/ubuntu/DICHE-git/logs
cat ./access.log | grep \"dbid: > ./archives/`date +'%y_%m_%d'`
echo > ./access.log
cat ./archives/* > ./trace.log

