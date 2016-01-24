#!/usr/bin/env python2
# from https://thepacketgeek.com/give-exabgp-an-http-api-with-flask/

from flask import Flask, request
from sys import stdout

app = Flask(__name__)


# Setup a command route to listen for prefix advertisements
@app.route('/', methods=['POST'])
def command():
    command = request.form['command']
    stdout.write('%s\n' % command)
    stdout.flush()

    return '%s\n' % command

if __name__ == '__main__':
    app.run()
