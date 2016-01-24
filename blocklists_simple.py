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


a = IPSet()
b = IPSet()
# how long should we sleep in minutes?
mins = 30
expires = ''
nexthop = ' next-hop 0.0.0.1 origin incomplete as-path [64666 64666 64666]\n'
#nexthop = ' next-hop self community [64512:666]\n'

blocklists = ['https://www.spamhaus.org/drop/drop.txt',
              'https://www.spamhaus.org/drop/edrop.txt',
              'https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt']


def makeprefix(ip):
	net = IP(ip, make_net=True)
	net.NoPrefixForSingleIp = None
	return net


def fetch():
	a = IPSet([])
	for blocklist in blocklists:
		r = requests.get(blocklist)
		for line in r.iter_lines():
			if linefilter(line):
				a.add(makeprefix(linefilter(line)))

	for prefix in b:
		if b.len() > 0 and b.__contains__(prefix) and not a.__contains__(prefix):
			stdout.write('withdraw route ' + str(prefix) + nexthop)
			stdout.flush()

	for prefix in a:
		stdout.write('announce route ' + str(prefix) + nexthop)
		stdout.flush()

	b.add(a)


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
		ip = line.split(' ')[0].split(';')[0].split('#')[0].strip().decode()
		return ip


while True:
	fetch()
	sleep(mins * 60)
