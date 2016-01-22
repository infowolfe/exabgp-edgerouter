#!/usr/bin/env python
# from https://thepacketgeek.com/processing-and-storing-bgp-messages-in-mongodb/

from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING

###  DB Setup ###
client = MongoClient()
db = client.exabgp_db
updates = db.bgp_updates


def peer_is_up(peer_ip):

    # Find keepalives in last 5 minutes, True or False based on count
    has_keepalives = bool(updates.find({'peer': peer_ip, 'time': {'$gt': datetime.now() - timedelta(minutes=5)}}).count())

    # Check latest state message for this peer
    state_message = list(updates.find({'type': 'state', 'peer': peer_ip}).sort('time', DESCENDING).limit(1))
    state = state_message[0]['state']

    if has_keepalives and state == 'up':
        return True
    else:
        return False

peer = '172.16.2.10'
peer_status = peer_is_up(peer)

if peer_status:
    print 'Peer %s is up.' % peer
else:
    print 'Peer %s is down.' % peer
