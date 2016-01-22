#!/usr/bin/env python2
# from https://thepacketgeek.com/control-bgp-advertisements-to-ebgp-peers-with-exabgp/ 

from sys import stdout, stdin
from time import sleep

# Print the command to STDIN so ExaBGP can execute
stdout.write('announce route 100.10.10.0/24 next-hop 10.0.0.2 local-preference 65000 community [100:100]\n')
stdout.flush()

#Keep the script running so ExaBGP doesn't stop running and tear down the BGP peering
while True:
    sleep(10)
