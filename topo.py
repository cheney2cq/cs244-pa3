#!/usr/bin/env python
# Written by CJ Cullen and Stephen Barber for CS 244 at Stanford, Spring 2014
from mininet.topo import Topo

class Wifi3GTopo(Topo):
    "Two hosts connected by a WiFi link and a 3G link"

    def __init__(self, bw_wifi, bw_3g, latency_wifi, latency_3g, loss_wifi, loss_3g, jitter_wifi, jitter_3g):
        super(Wifi3GTopo, self).__init__()

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')

        # WiFi link
        self.addLink(h1, s0, bw=bw_wifi, delay=latency_wifi, loss=loss_wifi, jitter=jitter_wifi, max_queue_size=1000)
        # 3G link
        self.addLink(h1, s1, bw=bw_3g, delay=latency_3g, loss=loss_3g, jitter=jitter_3g, max_queue_size=1000)

        self.addLink(s0, h2, bw=1000, delay='1ms', loss=0, max_queue_size=10)
        self.addLink(s1, h2, bw=1000, delay='1ms', loss=0, max_queue_size=10)

