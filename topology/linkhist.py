#!/usr/bin/env python3

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(__file__)+'/../helper')
from address_finder import *
from positions import *
from math import *
from Graph import *
from plot_topo import *
import argparse
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
import copy
import pandas as pd
import stats

def linkhist(f):
    paths = stats.stats(f)

    nodes = list(paths.keys())

    alldata = []
    for dst in nodes:
        for src in nodes:
            if src in paths[dst]:
                alldata.append(paths[dst][src]['mean'])

    r = range(int(round(min(alldata))),int(round(max(alldata)+1)))

    return np.histogram(alldata,r)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('file', metavar='FILE', nargs=1, help='the paths data json file to read')
    args = parser.parse_args()

    hist,bin_edges = linkhist(args.file[0])

    plt.bar(bin_edges[:-1],hist)
    plt.show()
