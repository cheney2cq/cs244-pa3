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
    else:
        filename = 'logfile_mptcp'

    diffs_file = open(filename, 'r')

    diffs = [int(diff) for diff in diffs_file.readlines()]
    diffs = sorted(diffs)

    lowest = diffs[0]
    highest = diffs[-1]

    num_buckets = 70

    bucketsize = (highest - lowest) / num_buckets + 1
    buckets = [0 for i in range(num_buckets)]

    for val in diffs:
        bucket = (val - lowest) / bucketsize
        buckets[bucket] += 1

    for i in range(num_buckets):
        buckets[i] /= float(len(diffs))

    ms_buckets = [lowest + x * bucketsize for x in range(num_buckets)]
    ms_x = np.linspace(ms_buckets[0], ms_buckets[-1], num_buckets)

    buckets_smooth = spline(ms_buckets, buckets, ms_x)

    matplotlib.pyplot.clf()
    matplotlib.pyplot.plot(ms_x, buckets_smooth)
    matplotlib.pyplot.savefig('pdf_smooth_%s.png' % type)

    matplotlib.pyplot.clf()
    matplotlib.pyplot.plot(ms_buckets, buckets)
    matplotlib.pyplot.savefig('pdf_%s.png' % type)

    matplotlib.pyplot.clf()
    matplotlib.pyplot.hist(diffs, num_buckets)
    matplotlib.pyplot.savefig('hist_%s.png' % type)

types = ['wifi', '3g', 'mptcp']

for type in types:
    plot_file(type)
