#!/usr/bin/env python
# from https://thepacketgeek.com/using-service-health-checks-to-automate-exabgp/#more-513 (part2.2)

from collections import namedtuple
import socket
from sys import stdout
from time import sleep


def is_alive(address, port):
    """ This is a function that will test TCP connectivity of a given
    address and port. If a domain name is passed in instead of an address,
    the socket.connect() method will resolve.

    address (str): An IP address or FQDN of a host
    port (int): TCP destination port to use

    returns (bool): True if alive, False if not
    """

    # Create a socket object to connect with
    s = socket.socket()

    # Now try connecting, passing in a tuple with address & port
    try:
        s.connect((address, port))
        return True
    except socket.error:
        return False
    finally:
        s.close()

# Add namedtuple object for easy reference below
TrackedObject = namedtuple('EndHost', ['address','port','prefix', 'nexthop'])
# Make a list of these tracked objects
tracked_objects = [
    TrackedObject('thepacketgeek.com', 80, '100.10.10.0/24', 'self'),
    TrackedObject('8.8.8.8', 53, '200.20.20.0/24', 'self'),
]

while True:
    for host in tracked_objects:
        if is_alive(host.address, host.port):
            stdout.write('announce route %s next-hop %s\n' % (host.prefix, host.nexthop))
            stdout.flush()
        else:
            stdout.write('withdraw route %s next-hop %s\n' % (host.prefix, host.nexthop))
            stdout.flush()
    sleep(10)
