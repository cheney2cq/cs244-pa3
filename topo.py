#!/usr/bin/env python
from mininet.topo import Topo


class Wifi3GTopo(Topo):
    "Two hosts connected by a WiFi link and a 3G link"

    def __init__(self, **opts):
        super(Wifi3GTopo, self).__init__(**opts)

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # WiFi link
        self.addLink(h1, h2, bw=8, delay='10ms', loss=5, max_queue_size=10)
        # 3G link
        self.addLink(h1, h2, bw=2, delay='75ms', loss=15, max_queue_size=64)

