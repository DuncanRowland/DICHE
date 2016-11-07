#!/bin/sh

#Edit /etc/sudoers.d (e.g. copy root for ubuntu)

sudo iptables -A INPUT -s $1 -j DROP

