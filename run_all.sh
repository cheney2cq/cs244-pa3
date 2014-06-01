#!/bin/sh -e
# Run all tests for MPTCP latency over WiFi/3G
# Written by CJ Cullen and Stephen Barber for CS 244 at Stanford, Spring 2014

# Check that this was invoked as root
if [ "`id -u`" -ne 0 ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

# Clean up any subprocesses left lying around
trap "set +e; trap - INT HUP TERM; kill 0; exit 1" INT HUP TERM

# Run standard tests
python2 run.py
python2 plot.py

# Run tests with higher jitter
for jitter in 150 200 250; do
    python2 run.py --jitter-3g="$jitter"
    python2 plot.py "j$jitter"
done
