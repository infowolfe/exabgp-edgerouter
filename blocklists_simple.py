#!/usr/bin/env python
# encoding utf-8
"""
exabgp: aggregate_requests.py
based partially on aggregate.py from https://adamkuj.net/blog/2014/04/08/a-utility-to-perform-ipv4-ipv6-prefix-aggregation/
"""

from IPy import IP, IPSet
import requests
import socket
from sys import stdout
from time import sleep

n = IPSet()
# how long should we sleep in minutes?
mins = 30
expires = ''

blocklists = [ 'https://www.spamhaus.org/drop/drop.txt',
               'https://www.spamhaus.org/drop/edrop.txt',
               'https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt' ]

def fetch():
	for blocklist in blocklists:
		r = requests.get(blocklist)
		for line in r.iter_lines():
			if linefilter(line):
				net = IP(linefilter(line),make_net=True)
				net.NoPrefixForSingleIp = None
				n.add(net)

	for prefix in n:
		stdout.write('announce route ' + str(prefix) + ' next-hop 0.0.0.1 origin incomplete as-path [64666 64666 64666]\n')
		#stdout.write('announce route ' + str(prefix) + ' next-hop self community [64512:666]\n')
		stdout.flush()

def linefilter(line):
	if line.startswith(';'):
		if line.startswith('; Expires:'):
			expires = line.lstrip('; Expires: ')
		else:
			pass
		pass
	elif line.startswith('#'):
		pass
	else:
		a = line.split(' ')[0].split(';')[0].split('#')[0].strip().decode()
		return a

while True:
	fetch()
	sleep(mins * 60)
