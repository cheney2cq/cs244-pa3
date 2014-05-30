MPTCP application latency experiment over WiFi/3G
=================================================

Purpose
-------
Replicate Figure 7 of the NSDI paper [How Hard Can It Be? Designing and Implementing a Deployable Multipath TCP](https://www.usenix.org/conference/nsdi12/technical-sessions/presentation/raiciu).

This work was done by CJ Cullen and Stephen Barber for [CS 244](http://cs244.stanford.edu).

The associated blog post is located on the [Reproducing Network Research blog](http://reproducingnetworkresearch.wordpress.com/2014/05/29/cs-244-14-mptcp-latency-on-wifi3g/).

Running the experiment on Amazon EC2
------------------------------------
This experiment is published on Amazon EC2 under *ami to be determined*. We used
a c3.large instance - results may vary depending on the instance.

Running the experiment is simple - in the pa3 directory, do
```sh
sudo python run.py
python plot.py
python -m SimpleHTTPServer
```

The resulting plot of the probability density function for application latency
is stored in `pdf_smooth_all.png`.

Running the experiment from scratch
-----------------------------------
Our base setup was Ubuntu 14.04 LTS. On top of this, a custom kernel and mininet
need to be installed, along with the code for the experiment.

We used a snapshot of the MPTCP kernel dated May 19, 2014, and applied a patch
(`add_sysctls.patch`) to add support for sysctls that disable mechanisms 1 and 2
from the NSDI paper. The patch applies cleanly against commit
`2c005d975695b925f21248a11a5d1afed392ee2e` in the `mptcp_trunk` branch of the
[MPTCP kernel git repository](https://github.com/multipath-tcp/mptcp).

The following kernel config settings must be set in order to use MPTCP:
```
CONFIG_MPTCP=y
CONFIG_MPTCP_PM_ADVANCED=y
CONFIG_MPTCP_FULLMESH=y
CONFIG_MPTCP_NDIFFPORTS=y
CONFIG_DEFAULT_MPTCP_PM="fullmesh"
```

A sample kernel config (`config-3.14.0-mptcp`) is included for convenience.

A patch (mininet-loss-rate.patch) is included for mininet to add support for
non-integer link loss rates.
This should apply cleanly against commit
`5797f5852ec2edf31ce3e0986b6ba15e95ecfd37` in the `master` branch of
[mininet](https://github.com/mininet/mininet). After applying the patch, mininet
should be installed with the util/install.sh script.

Tweakable values
----------------
`topo.py` contains the topology for the experiment - link loss rates, bandwidth,
latency, and jitter can be set here.

`client.c` has defined constants for TCP send buffer size (default 200 KB) and the time to run
the experiment (default 100 seconds).

`server.c` has a defined constant for the TCP receive buffer size (default 30
KB).

