#!/bin/bash

#Run 'melt' command save pid until process to finishes
pidfile="$1/.meltpid"
vidfile="$1/DICHE.mp4"
tmpfile="$1/.DICHE.mp4"
rm -f "$vidfile"
melt "${@:2}" -silent &> /dev/null &
meltpid=$!
echo $meltpid > "$pidfile"
wait $meltpid
mv "$tmpfile" "$vidfile"
rm -f $pidfile
exit 0
