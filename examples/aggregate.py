#!/usr/bin/python
# from https://adamkuj.net/blog/2014/04/08/a-utility-to-perform-ipv4-ipv6-prefix-aggregation/ 
"""
ALK 2014-04-08
aggregate.py: IPv4 & IPv6 replacement (in spirit) for Joe Abley's 'aggregate' command
note: not a drop-in replacement for the original 'aggregate' command - command line flags are different 
requirements: IPy class (debian: python-ipy package)
 
input: list of IPv4 and/or IPv6 addresses and/or subnets (filename or STDIN)
output: aggregated list if subnets (STDOUT)
 
options:
--host|-h: convert host addresses w/o masks to IPv4 /32 or IPv6 /128 networks when sending output 
    i.e. 192.0.2.10 becomes 192.0.2.10/32
    i.e. 2001:db8:abcd:1234::d00d becomes 2001:db8:abcd:1234::d00d/128)
    note: hosts (w/o mask specified) are *always* permitted in the input, and will be auto-aggregated 
--cidr|-c: convert IPv4 classfull networks without netmasks to proper cidr subnets
    i.e. Class A: 10.0.0.0 becomes 10.0.0.0/8 (but 10.1.0.0 fails, unless -h is used to make it 10.1.0.0/32)
    i.e. Class B: 172.24.0.0 becomes 172.24.0.0/16 (but 172.24.10.0 fails, unless -h is used to make a /32)
    i.e. Class C: 192.0.0.0 becomes 192.0.0.0/24) 
if -h and -c are used concurrenty:
    -c is evaluated first (otherwise anything w/o a mask would be considered a host prefix)
--truncate|-t: prune the network portion to match the netmask
   (i.e. 1.2.3.4/24 becomes 1.2.3.0/24)
   (i.e. 2001:db8:abcd:1234::dead:beef/64 becomes 2001:db8:abcd:1234::/64
--ipv4|-4 or --ipv6|-6: display only IPv4 or only IPv6 prefixes 
--ignore|-i: ignore lines that can't be parsed (otherwise, program will exit w/ error)
"""
 
from IPy import IP, IPSet
import argparse
import fileinput
import sys
 
parser = argparse.ArgumentParser(conflict_handler='resolve')
 
parser.add_argument('-t', '--truncate', action='store_true', dest='truncate', help='truncate the network portion of the prefix to match the netmask (i.e. 192.0.2.10/24 becomes 192.0.2.0/24)', default=False) 
parser.add_argument('-h', '--host', action='store_true', dest='host', help='convert host addresses w/o masks to IPv4 /32 or IPv6 /128 networks', default=None)
parser.add_argument('-c', '--cidr', dest='cidr', action='store_true', help='add netmasks to classful IPv4 network definitions')
parser.add_argument('-i', '--ignore-errors', dest='ignore', action='store_true', help='discard malformed input lines instead of exiting', default=False)
version = parser.add_mutually_exclusive_group()
version.add_argument('-4', '--ipv4', dest='ipv6', action='store_false', help='display only IPv4 prefixes (default: show IPv4 & IPv6)', default=True)
version.add_argument('-6', '--ipv6', dest='ipv4', action='store_false', help='display only IPv6 prefixes (default: show IPv4 & IPv6)', default=True)
parser.add_argument('args', nargs=argparse.REMAINDER, help='<input file> or STDIN')
args=parser.parse_args()
 
s = IPSet() # the set of aggregated addresses
 
try:
  for line in fileinput.input(args.args):
    try:
      ip = IP(line,make_net=args.truncate) # read the line as an IP network; truncate if -t was specified 
    except ValueError as err: # exception if the line can't be parsed as an IP prefix
      if args.ignore == False:
        print(err)
        print "exiting..."
        sys.exit(1)
 
    # process -c option
    if args.cidr:
      if ip in IP('0.0.0.0/1') and ( ip.int() & 0x00ffffff == 0x00000000 ) and ip.prefixlen() == 32:
        ip=ip.make_net(8)
      if ip in IP('128.0.0.0/2') and ( ip.int() & 0x0000ffff == 0x00000000 ) and ip.prefixlen() == 32:
        ip=ip.make_net(16)
      if ip in IP('192.0.0.0/3') and ( ip.int() & 0x000000ff == 0x00000000 ) and ip.prefixlen() == 32:
        ip=ip.make_net(24)
 
    # process -h option
    if args.host:
      ip.NoPrefixForSingleIp = None
 
    s.add(ip) # add the IP into the set, automatically aggregating as necessary
 
except KeyboardInterrupt:  # show usage if user exits w/ CTRL-C 
  print
  parser.print_help()
  sys.exit(1)
 
# send the results to STDOUT
for prefix in s:
  if args.ipv4 & (prefix.version() == 4):
      print (prefix)
  if args.ipv6 & (prefix.version() == 6):
      print (prefix)
