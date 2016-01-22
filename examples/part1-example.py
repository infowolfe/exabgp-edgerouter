#!/usr/bin/env python2
# from https://thepacketgeek.com/influence-routing-decisions-with-python-and-exabgp/#more-522 (part 1)

from sys import stdout
from time import sleep

messages = [
'announce route 100.10.0.0/24 next-hop self community [64512:666]',
'announce route 101.10.0.0/24 next-hop self community [64512:666]'
]

sleep(5)

for message in messages:
    stdout.write(message + '\n')
    stdout.flush()
    sleep(1)

while True:
    sleep(1)
