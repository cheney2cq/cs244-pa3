#!/usr/bin/python
# Written by CJ Cullen and Stephen Barber for CS 244 at Stanford, Spring 2014
# Partially based on code from AMI ID ami-9e7ce9ae from an earlier quarter

import os
import signal
import sys
from subprocess import Popen, PIPE
from time import sleep
import termcolor as T
import argparse

from mininet.net import Mininet
from mininet.log import lg
from mininet.node import OVSKernelSwitch as Switch
from mininet.link import Link, TCLink
from mininet.util import makeNumeric, custom

from topo import Wifi3GTopo

from argparse import ArgumentParser

parser = ArgumentParser(description="MPTCP WiFi/3G Latency tests")
parser.add_argument('--bw-wifi',
                    dest="bw_wifi",
                    type=float,
                    action="store",
                    help="Bandwidth of WiFi link (Mbps)",
                    default=30)

parser.add_argument('--bw-3g',
                    dest="bw_3g",
                    type=float,
                    action="store",
                    help="Bandwidth of 3G link (Mbps)",
                    default=3)

parser.add_argument('--latency-wifi',
                    dest="latency_wifi",
                    type=float,
                    action="store",
                    help="Latency of WiFi link (ms)",
                    default=5)

parser.add_argument('--latency-3g',
                    dest="latency_3g",
                    type=float,
                    action="store",
                    help="Latency of 3G link (ms)",
                    default=30)

parser.add_argument('--loss-wifi',
                    dest="loss_wifi",
                    type=float,
                    action="store",
                    help="Loss rate of WiFi link (0.0-1.0)",
                    default=0.75)

parser.add_argument('--loss-3g',
                    dest="loss_3g",
                    type=float,
                    action="store",
                    help="Loss rate of 3G link (0.0-1.0)",
                    default=0.1)

parser.add_argument('--jitter-wifi',
                    dest="jitter_wifi",
                    type=float,
                    action="store",
                    help="Jitter of WiFi link (ms)",
                    default=0.0)

parser.add_argument('--jitter-3g',
                    dest="jitter_3g",
                    type=float,
                    action="store",
                    help="Jitter of 3G link (ms)",
                    default=100.0)

args = parser.parse_args()

net = None

def signal_cleanup(signum, frame):
    if net is not None:
        net.stop()
    sys.exit(1)

def sysctl_set(key, value):
    """Issue systcl for given param to given value and check for error."""
    p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE,
              stderr=PIPE)
    # Output should be empty; otherwise, we have an issue.
    stdout, stderr = p.communicate()
    stdout_expected = "%s = %s\n" % (key, value)
    if stdout != stdout_expected:
        raise Exception("Popen returned unexpected stdout: %s != %s" %
                        (stdout, stdout_expected))
    if stderr:
        raise Exception("Popen returned unexpected stderr: %s" % stderr)


def set_mptcp_enabled(enabled):
    """Enable MPTCP if true, disable if false"""
    e = 1 if enabled else 0
    lg.info("setting MPTCP enabled to %s\n" % e)
    sysctl_set('net.mptcp.mptcp_enabled', e)

def set_optimizations_enabled(enabled):
    """Enable MPTCP optimizations if true, disable if false"""
    e = 1 if enabled else 0
    lg.info("setting MPTCP opts to %s\n" % e)
    sysctl_set('net.mptcp.mptcp_rbuf_opti', e)
    sysctl_set('net.mptcp.mptcp_rbuf_penal', e)
    sysctl_set('net.mptcp.mptcp_rbuf_retr', e)

def setup(mptcp, optimizations):
    set_mptcp_enabled(mptcp)
    set_optimizations_enabled(optimizations)

def run(mptcp, net, type):
    if type == 'wifi':
        log = 'logfile_wifi'
        ip = '10.0.0.4'
    elif type == '3g':
        log = 'logfile_3g'
        ip = '10.0.1.4'
    else:
        if type == 'mptcp_noopt':
            log = 'logfile_mptcp_noopt'
        else:
            log = 'logfile_mptcp'
        ip = '10.0.0.4'

    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')

    for i in range(2):
        # Setup IPs:
        h1.cmdPrint('ifconfig h1-eth%i 10.0.%i.3 netmask 255.255.255.0' % (i, i))
        h2.cmdPrint('ifconfig h2-eth%i 10.0.%i.4 netmask 255.255.255.0' % (i, i))

        h1.cmdPrint('ifconfig h1-eth%i txqueuelen 50' % (i, ))
        h2.cmdPrint('ifconfig h2-eth%i txqueuelen 50' % (i, ))

        if mptcp:
            lg.info("configuring source-specific routing tables for MPTCP\n")
            # This creates two different routing tables, that we use based on the
            # source-address.
            dev = 'h1-eth%i' % i
            table = '%s' % (i + 1)
            h1.cmdPrint('ip rule add from 10.0.%i.3 table %s' % (i, table))
            h1.cmdPrint('ip route add 10.0.%i.0/24 dev %s scope link table %s' % (i, dev, table))
            h1.cmdPrint('ip route add default via 10.0.%i.1 dev %s table %s' % (i, dev, table))

    # verify connectivity with a ping test.
    lg.info("pinging each destination interface\n")
    for i in range(2):
        h2_out = h2.cmd('ping -c 3 10.0.%i.3' % i)
        lg.info("ping test output: %s\n" % h2_out)

    lg.info("%s: starting server and client\n" % type)
    h2.sendCmd('./server %s' % log)

    cmd = './client %s' % ip
    h1.cmd(cmd)
    h1_out = h1.waitOutput()
    sleep(2)  # hack to wait for server to finish
    out = h2.read(10000)
    lg.info("%s run completed" % type)
    return None


def end():
    set_mptcp_enabled(False)

def genericTest(topo, setup, run, end, type):
    global net
    if type == 'wifi' or type == '3g':
        mptcp = False
    else:
        mptcp = True

    if type == 'mptcp_noopt':
        optimizations = False
    else:
        optimizations = True

    signal.signal(signal.SIGABRT, signal_cleanup)
    signal.signal(signal.SIGHUP, signal_cleanup)
    signal.signal(signal.SIGINT, signal_cleanup)
    signal.signal(signal.SIGTERM, signal_cleanup)

    net = Mininet(topo=topo, link=TCLink)
    setup(mptcp, optimizations)
    net.start()
    data = run(mptcp, net, type)
    net.stop()
    end()
    return data


def main():
    lg.setLogLevel('info')
    topo = Wifi3GTopo(bw_wifi=args.bw_wifi,
                      bw_3g=args.bw_3g,
                      latency_wifi='%fms' % (args.latency_wifi,),
                      latency_3g='%fms' % (args.latency_3g,),
                      loss_wifi=args.loss_wifi,
                      loss_3g=args.loss_3g,
                      jitter_wifi='%fms' % (args.jitter_wifi,),
                      jitter_3g='%fms' % (args.jitter_3g,))

    # Compile client and server
    os.system('gcc server.c -o server')
    os.system('gcc client.c -o client')

    types = [ 'wifi', '3g', 'mptcp', 'mptcp_noopt' ]
    for type in types:
        print "Running", type
        genericTest(topo, setup, run, end, type)


if __name__ == '__main__':
    main()
