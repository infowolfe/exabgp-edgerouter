#!/usr/bin/env python
# from https://thepacketgeek.com/using-service-health-checks-to-automate-exabgp/#more-513 (part2.1)

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
 
while True:
    if is_alive('thepacketgeek.com', 80):
        stdout.write('announce route 100.10.10.0/24 next-hop self' + '\n')
        stdout.flush()
    else:
        stdout.write('withdraw route 100.10.10.0/24 next-hop self' + '\n')
        stdout.flush()
    sleep(10)
