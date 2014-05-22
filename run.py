#!/usr/bin/python
import os
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

def setup(mptcp):
    set_mptcp_enabled(mptcp)

def run(mptcp, net, type):
    if type == 'wifi':
        log = 'logfile_wifi'
        ip = '10.0.0.4'
    elif type == '3g':
        log = 'logfile_3g'
        ip = '10.0.1.4'
    else:
        log = 'logfile_mptcp'
        ip = '10.0.0.4'

    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')

    h1.cmdPrint('ifconfig')
    h2.cmdPrint('ifconfig')
    for i in range(2):
        # Setup IPs:
        h1.cmdPrint('ifconfig h1-eth%i 10.0.%i.3 netmask 255.255.255.0' % (i, i))
        h2.cmdPrint('ifconfig h2-eth%i 10.0.%i.4 netmask 255.255.255.0' % (i, i))

        h1.cmdPrint('ifconfig h1-eth%i txqueuelen 3' % (i, ))
        h2.cmdPrint('ifconfig h2-eth%i txqueuelen 3' % (i, ))

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
    if type == 'wifi' or type == '3g':
        mptcp = False
    else:
        mptcp = True

    net = Mininet(topo=topo, link=TCLink)
    setup(mptcp)
    net.start()
    data = run(mptcp, net, type)
    net.stop()
    end()
    return data


def main():
    lg.setLogLevel('info')
    topo = Wifi3GTopo()

    # Compile client and server
    os.system('gcc server.c -o server')
    os.system('gcc client.c -o client')

    types = [ 'wifi', '3g', 'mptcp' ]
    for type in types:
        print "Running", type
        genericTest(topo, setup, run, end, type)


if __name__ == '__main__':
    main()
