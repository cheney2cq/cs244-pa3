#!/usr/bin/env python
import matplotlib
matplotlib.use('Agg')
import pylab

import numpy as np
from scipy.interpolate import spline
def plot_file(type):
    if type == 'wifi':
        filename = 'logfile_wifi'
    elif type == '3g':
        filename = 'logfile_3g'
    elif type == 'mptcp_noopt':
        filename = 'logfile_mptcp_noopt'
    else:
        filename = 'logfile_mptcp'

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

#    matplotlib.pyplot.clf()
    matplotlib.pyplot.plot(ms_x, buckets_smooth, label=type)

#    matplotlib.pyplot.clf()
#    matplotlib.pyplot.plot(ms_buckets, buckets)
#    matplotlib.pyplot.savefig('pdf_%s.png' % type)
#
#    matplotlib.pyplot.clf()
#    matplotlib.pyplot.hist(diffs, num_buckets)
#    matplotlib.pyplot.savefig('hist_%s.png' % type)

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
matplotlib.pyplot.savefig('pdf_smooth_all.png')
