#!/usr/bin/env python
# Written by CJ Cullen and Stephen Barber for CS 244 at Stanford, Spring 2014
import matplotlib
matplotlib.use('Agg')
import pylab

import numpy as np
from scipy.interpolate import spline

import sys

def plot_file(type):
    filename = 'logfile_%s' % (type,)

    diffs_file = open(filename, 'r')

    diffs = [int(diff) for diff in diffs_file.readlines()]
    diffs = sorted(diffs)

    lowest = diffs[0]
    highest = diffs[-1]

    bucketsize = 20
    num_buckets = highest / bucketsize + 1
    buckets = [0 for i in range(num_buckets)]

    for val in diffs:
        bucket = (val - lowest) / bucketsize
        buckets[bucket] += 1

    for i in range(num_buckets):
        buckets[i] /= float(len(diffs))

    ms_buckets = [lowest + x * bucketsize for x in range(num_buckets)]
    ms_x = np.linspace(ms_buckets[0], ms_buckets[-1], num_buckets)

    buckets_smooth = spline(ms_buckets, buckets, ms_x)

    matplotlib.pyplot.plot(ms_x, buckets_smooth, label=type)

types = ['wifi', '3g', 'mptcp', 'mptcp_noopt']

matplotlib.pyplot.figure(figsize=(14, 6), dpi=200)
matplotlib.pyplot.xlim(0.0, 3000)
matplotlib.pyplot.ylim(0.0, 0.18)
matplotlib.pyplot.title('Application level latency for 3G/WiFi')
matplotlib.pyplot.xlabel('Latency (ms)')
matplotlib.pyplot.ylabel('PDF')

for type in types:
    plot_file(type)

matplotlib.pyplot.legend()
if len(sys.argv) > 1:
    out_filename = 'fig7_%s.png' % (sys.argv[1])
else:
    out_filename = 'fig7.png'

matplotlib.pyplot.savefig(out_filename)
