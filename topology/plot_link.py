#!/usr/bin/env python3

import numpy as np
import sys
from math import *
import argparse
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
import json
import sys
import os
sys.path.insert(0,os.path.dirname(__file__)+'/../helper')
from address_finder import *

def link(nodeA,nodeB,f):
    nodeA = format_address(nodeA)
    nodeB = format_address(nodeB)

    with open(f,"r") as infile:
        data = json.load(infile)
        paths_data = data['data']

    return paths_data[nodeA][nodeB],paths_data[nodeB][nodeA]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('nodeA')
    parser.add_argument('nodeB')
    parser.add_argument('file', metavar='FILE', nargs=1, help='the paths data json file to read')
    args = parser.parse_args()

    ab,ba = link(args.nodeA,args.nodeB,args.file[0])

    # Generate Histogram
    path_loss_range = list(range(1,102))
    plt.figure(figsize=(10,2))
    n, bins, patches = plt.hist(ab, path_loss_range, normed=False, alpha=0.75)
    n, bins, patches = plt.hist(ba, path_loss_range, normed=False, alpha=0.75)
    plt.show()
