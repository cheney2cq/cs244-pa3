#!/usr/bin/python
"""
Test to validate MPTCP operation across at least two links.
"""

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

# TODO: move to common location; code shared with DCTCP.
def progress(t):
    while t > 0:
        print T.colored('  %3d seconds left  \r' % (t), 'cyan'),
        t -= 1
        sys.stdout.flush()
        sleep(1)
    print '\r\n'

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


def set_mptcp_ndiffports(ports):
    """Set ndiffports, the number of subflows to instantiate"""
    lg.info("setting MPTCP ndiffports to %s\n" % ports)
    sysctl_set("net.mptcp.mptcp_ndiffports", ports)


def setup(mptcp):
    set_mptcp_enabled(mptcp)
    set_mptcp_ndiffports(1)


def run(mptcp, net):
    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')

    for i in range(2):
        # Setup IPs:
        h1.cmdPrint('ifconfig h1-eth%i 10.0.%i.3 netmask 255.255.255.0' % (i, i))
        h2.cmdPrint('ifconfig h2-eth%i 10.0.%i.4 netmask 255.255.255.0' % (i, i))

        if mptcp:
            lg.info("configuring source-specific routing tables for MPTCP\n")
            # This creates two different routing tables, that we use based on the
            # source-address.
            dev = 'h1-eth%i' % i
            table = '%s' % (i + 1)
            h1.cmdPrint('ip rule add from 10.0.%i.3 table %s' % (i, table))
            h1.cmdPrint('ip route add 10.0.%i.0/24 dev %s scope link table %s' % (i, dev, table))
            h1.cmdPrint('ip route add default via 10.0.%i.1 dev %s table %s' % (i, dev, table))

    # TODO: expand this to verify connectivity with a ping test.
    lg.info("pinging each destination interface\n")
    for i in range(2):
        h2_out = h2.cmd('ping -c 1 10.0.%i.3' % i)
        lg.info("ping test output: %s\n" % h2_out)

    lg.info("starting server")
    h2.sendCmd('./server logfile')

    cmd = './client 10.0.0.4'
    h1.cmd(cmd)
    h1_out = h1.waitOutput()
    lg.info("client output:\n%s\n" % h1_out)
    sleep(0.1)  # hack to wait for iperf server output.
    out = h2.read(10000)
    lg.info("server output: %s\n" % out)
    return None


def end():
    set_mptcp_enabled(False)
    set_mptcp_ndiffports(1)


def genericTest(topo, setup, run, end):
    net = Mininet(topo=topo)
    setup()
    net.start()
    data = run(True, net)
    net.stop()
    end()
    return data


def main():
    lg.setLogLevel('info')
    topo = Wifi3GTopo()
    genericTest(topo, setup, run, end)


if __name__ == '__main__':
    main()
