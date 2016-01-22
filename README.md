## Introduction
This README and software enable automated external blacklisting of ip addresses listed on the Spamhaus [DROP and EDROP](https://www.spamhaus.org/drop/) lists, and the [Emerging Threats](http://www.emergingthreats.net) aggregated blocklist by [Ubiquiti EdgeRouter](https://www.ubnt.com/products/#broadband/routing) family compatible devices (and perhaps Vyatta-compatible vRouters).

## Quickstart ExaBGP for ERLite ip-blocklisting
 * Setup EdgeRouter BGP (documented below if not already complete)
 * `git clone https://github.com/infowolfe/exabgp-edgerouter.git`
 * `pip install -r requirements.txt` or if you have native packages for your OS/Distro you're welcome to use them instead (Gentoo: `emerge -bqva exabgp ipy requests`)
 * Edit `conf.ini` to match EdgeRouter setup
 * Edit `blocklists_simple.py` to include preferred lists and to suit
 * Run `exabgp ./conf.ini` and issue `show ip bgp sum` and `show ip bgp route-map blackhole` to verify routes are in table.
 
## EdgeRouter configuration notes
 * Select a unique Autonomous System Number (ASN) between 64512-65534 ([RFC6996](http://tools.ietf.org/html/rfc6996)), this cannot be the same as the ASN for any of your peers/neighbors unless they're part of your network preferably share the same netblocks. We use `AS64512` and `AS64513` for our office EdgeRouters as per AWS VPC IPSEC VPN configuration defaults. AWS uses their ARIN issued `AS7224`. We're using `AS64666` in the `as-path-list` for our blackhole routes, though in theory you could use a community of `[$YOURAS:666]` (`[AS64512:666]`) if the EdgeRouter's `route-map foo rule N match community community-list blackhole` statements were working in 1.8.0b3.
 * We'll be using netblock `192.16.0.0/24` for this documentation and `192.168.0.1` as our EdgeRouter, `192.168.0.2` as our Linux/BSD/OS X host running ExaBGP. This will very likely not be the netblock you're using, so please substitute the correct netblocks/ips for your setup. We also use the semi-special and very unreachable `0.0.0.1/32` as the `next-hop` for our blackhole.
 * I'll be publishing both what the configuration would look like the form `show protocols bgp` from the `configure` context and at the bottom the list of commands similar to `set protocols bgp neighbor 192.168.0.2 remote-as 64512` via the `show configuration commands` from the `exec` (default) context.
 * `policy prefix-list rfc1918` is generally safe to bring **inbound**, but you will want to filter what prefixes you push **outbound** if you're setting up a multi-site/multi-prefix IPSEC VPN. I currently filter all of `rfc1918-192`, `rfc1918-172` and only `permit` `rfc-1918-10` if `le 24` for my home outbound (`10.10.0.0/24`).

## Files 
### `conf.ini`:
> `conf.ini` may be `chmod 755`'d if you wish to run `exabgp` from within `$PATH`     
> `run ...` may be shortened by `chmod 755 aggregate_requests.py`  

```
#!/usr/bin/env exabgp
group AS64512 {
	router-id 192.168.0.2;
	local-as 64512;
	local-address 192.168.0.2;
	peer-as 64512;

	neighbor 192.168.0.1 {
		family {
			inet4 unicast;
			inet4 multicast;
		}
	}

	family {
		inet4 unicast;
		inet4 multicast;
	}

	process droproutes {
		run /usr/bin/env python2 /path/to/exabgp/blocklists_simple.py;
	}
}
```

### `blocklists_simple.py`:
> The variable `mins` should be set to your preferred TTL, I recommend no shorter than 30 minutes.  
> The `blocklists` list can contain URLs to any lists with either standard dot-notation singular ips (`192.168.0.1`) or to cidr notation hosts (`192.168.0.1/32`) or networks (`192.168.0.0/16`). These lists will be combined, deduplicated, and aggregated before being output into the published routing table. This means that if you list `100.10.0.25`, `100.10.0.0/25`, `100.10.1.0/24`, and `100.10.0.0/24` only `100.10.0.0/23` will make it into the routing table. Lines starting with ; and # will be ignored and lines where ; # or ' ' exist between the ip or netblock and end of line should be stripped.

### 

## EdgeRouter `show` configuration
**Note: this is far from comprehensive. There are other options you may need or want that aren't listed here. We do the configuration in 3 stages, with only the relevant additions shown per stage. Stage 3 is entirely optional**

### Stage 1:
> from `[edit policy prefix-list exabgp rule 1]`  
> `le 32` Prefix length to match a netmask less than or equal to it  
> `prefix 0.0.0.0/0` Prefix to match (We want to accept all prefixes in ipv4 space from this neighbor)  
> from `[edit protocols bgp 64512 neighbor 192.168.0.2]`  
> `allowas-in 2` Accept a route that contains the local-AS in the as-path  
> `prefix-list exabgp` Prefix-list to filter route updates to/from this neighbor  

```
infowolfe@erlite# show
 policy {
     prefix-list exabgp {
         rule 1 {
             action permit
             le 32
             prefix 0.0.0.0/0
         }
     }
 }
 protocols {
     bgp 64512 {
         neighbor 192.168.0.2 {
             allowas-in {
                 number 2
             }
             prefix-list {
                 export exabgp
                 import exabgp
             }
             remote-as 64512
         }
         network 192.168.0.0/24 {
         }
         parameters {
             router-id 192.168.0.1
         }
     }
     static {
         route 0.0.0.1/32 {
             blackhole {
             }
         }
     }
 }
```
### Stage 2:
```
infowolfe@erlite# show
 policy {
     as-path-list blackhole {
         description "blackhole as-path-list"
         rule 1 {
             action permit
             regex "64666 64666 64666"
         }
     }
     route-map blackhole {
         description "blackholing, one community at a time"
         rule 1 {
             action permit
             match {
                 as-path blackhole
                 origin incomplete
             }
             set {
                 ip-next-hop 0.0.0.1
             }
         }
     }
 }
 protocols {
     bgp 64512 {
         neighbor 192.168.0.2 {
             route-map {
                 import blackhole
             }
         }
     }
 }
```
### Stage 3: (optional)
```
infowolfe@erlite# show
 policy {
     community-list 166 {
         description "blackhole community"
         rule 1 {
             action permit
             regex 64512:666
         }
     }
     prefix-list rfc1918 {
         rule 10 {
             action permit
             description rfc1918-192
             le 24
             prefix 192.168.0.0/16
         }
         rule 20 {
             action permit
             description rfc1918-172
             le 24
             prefix 172.16.0.0/12
         }
         rule 30 {
             action permit
             description rfc1918-10
             le 24
             prefix 10.0.0.0/8
         }
     }
 }
 protocols {
     bgp 64512 {
         neighbor 192.168.0.2 {
             soft-reconfiguration {
                 inbound
             }
         }
         parameters {
             graceful-restart {
                 stalepath-time 120
             }
             log-neighbor-changes
         }
     }
 }
 system {
     config-management {
         commit-revisions 1024
     }
     offload {
         ipsec enable
         ipv4 {
             forwarding enable
             gre enable
             pppoe enable
             vlan enable
         }
         ipv6 {
             forwarding enable
             vlan enable
         }
     }
     options {
         reboot-on-panic true
     }
     time-zone UTC
 }
```

## EdgeRouter `set` configuration commands
### Stage 1:
```
set policy prefix-list exabgp rule 1 action permit
set policy prefix-list exabgp rule 1 le 32
set policy prefix-list exabgp rule 1 prefix 0.0.0.0/0
set protocols bgp 64512 neighbor 192.168.0.2 allowas-in number 2
set protocols bgp 64512 neighbor 192.168.0.2 prefix-list export exabgp
set protocols bgp 64512 neighbor 192.168.0.2 prefix-list import exabgp
set protocols bgp 64512 neighbor 192.168.0.2 remote-as 64512
set protocols bgp 64512 network 192.168.0.0/24
set protocols bgp 64512 parameters router-id 192.168.0.1
set protocols static route 0.0.0.1/32 blackhole
compare
commit
```
### Stage 2:
```
set policy as-path-list blackhole description 'blackhole as-path-list'
set policy as-path-list blackhole rule 1 action permit
set policy as-path-list blackhole rule 1 regex '64666 64666 64666'
set policy route-map blackhole description 'blackholing, one community at a time'
set policy route-map blackhole rule 1 action permit
set policy route-map blackhole rule 1 match as-path blackhole
set policy route-map blackhole rule 1 match origin incomplete
set policy route-map blackhole rule 1 set ip-next-hop 0.0.0.1
set protocols bgp 64512 neighbor 192.168.0.2 route-map import blackhole
compare
commit
```
### Stage 3: (optional)
```
set policy community-list 166 description 'blackhole community'
set policy community-list 166 rule 1 action permit
set policy community-list 166 rule 1 regex '64512:666'
set policy prefix-list rfc1918 rule 10 action permit
set policy prefix-list rfc1918 rule 10 description rfc1918-192
set policy prefix-list rfc1918 rule 10 le 24
set policy prefix-list rfc1918 rule 10 prefix 192.168.0.0/16
set policy prefix-list rfc1918 rule 20 action permit
set policy prefix-list rfc1918 rule 20 description rfc1918-172
set policy prefix-list rfc1918 rule 20 le 24
set policy prefix-list rfc1918 rule 20 prefix 172.16.0.0/12
set policy prefix-list rfc1918 rule 30 action permit
set policy prefix-list rfc1918 rule 30 description rfc1918-10
set policy prefix-list rfc1918 rule 30 le 24
set policy prefix-list rfc1918 rule 30 prefix 10.0.0.0/8
set protocols bgp 64512 neighbor 192.168.0.2 soft-reconfiguration inbound 
set protocols bgp 64512 parameters graceful-restart stalepath-time 120
set protocols bgp 64512 parameters log-neighbor-changes
set system config-management commit-revisions 1024
set system offload ipsec enable
set system offload ipv4 forwarding enable
set system offload ipv4 gre enable
set system offload ipv4 pppoe enable
set system offload ipv4 vlan enable
set system offload ipv6 forwarding enable
set system offload ipv6 vlan enable
set system options reboot-on-panic true
set system time-zone UTC
compare
commit
```

## Credits
This collection was put together by [Chip Parker](https://github.com/infowolfe) (infowolfe+exabgp@gmail.com / infowolfe on freenode) while on the clock for [Enthought](https://enthought.com/) from information found at [PacketLife](https://thepacketgeek.com/series/influence-routing-decisions-with-python-and-exabgp/), at the excellent [ExaBGP wiki](https://github.com/Exa-Networks/exabgp/wiki), and uses an [IPy](https://github.com/autocracy/python-ipy/) technique he discovered within [aggregate.py](https://adamkuj.net/blog/2014/04/08/a-utility-to-perform-ipv4-ipv6-prefix-aggregation/). Since I'm not sure about the licensing of what I used, unless restricted by the above sources this software is public domain, no warranties for any particular purpose, etc. All code that this was derived from included in the `examples/` directory, with a link back in the header.