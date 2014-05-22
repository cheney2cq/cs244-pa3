#!/usr/bin/env python
from mininet.topo import Topo

class Wifi3GTopo(Topo):
    "Two hosts connected by a WiFi link and a 3G link"

    def __init__(self, **opts):
        super(Wifi3GTopo, self).__init__(**opts)

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')

        # WiFi link
        self.addLink(h1, s0, bw=10, delay='10ms', loss=1.5, jitter='2ms', max_queue_size=1000)
        # 3G link
        self.addLink(h1, s1, bw=2, delay='75ms', loss=0.75, jitter='15ms', max_queue_size=1000)

        self.addLink(s0, h2, bw=1000, delay='1ms', loss=0, max_queue_size=10)
        self.addLink(s1, h2, bw=1000, delay='1ms', loss=0, max_queue_size=10)

