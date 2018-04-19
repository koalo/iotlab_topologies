#!/usr/bin/env python3

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(__file__)+'/../helper')
from math import *
import argparse
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
import copy
import pandas as pd
import json
import stats

def nodedeg(f,degsteps=None):
    #path_loss_range = range(1,102)
    path_loss_range = range(20,94)

    paths = stats.stats(f)

    # Generate node degree for given maximum path loss
    nodes = list(paths.keys())
    links = 0

    if not degsteps:
        degsteps = [0,1,2,4,8,16,float('inf')]
        degsteps = [x for x in degsteps if x < len(nodes) or x == float('inf')]

    degreedist = [[0]*len(path_loss_range) for _ in range(len(degsteps))]
    for dst in nodes:
        for i in range(0,len(path_loss_range)):
            max_path_loss = path_loss_range[i]

            degree = len([x for x in paths[dst].values() if x['maxmean'] <= max_path_loss])
            if degree <= degsteps[0]:
                degreedist[0][i] += 1
            else:
                for j in range(1,len(degsteps)):
                    min_degree = degsteps[j-1]
                    max_degree = degsteps[j]
                    if min_degree < degree <= max_degree:
                        degreedist[j][i] += 1
                        break

    return degsteps,path_loss_range,degreedist

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('file', metavar='FILE', nargs=1, help='the paths data json file to read')
    args = parser.parse_args()
    degsteps,path_loss_range,degreedist = nodedeg(args.file[0])

    plt.figure(figsize=(10,2))
    bottom = [0]*len(path_loss_range)

    jet = plt.get_cmap('jet') 
    cNorm  = colors.Normalize(vmin=0, vmax=len(degsteps)-2)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

    for j in range(0,len(degsteps)-1):
        min_degree = degsteps[j]
        max_degree = degsteps[j+1]
        
        plt.bar(path_loss_range, degreedist[j], bottom=bottom, color=scalarMap.to_rgba(j), label="%.0f <= D < %.0f"%(min_degree,max_degree))

        for i in range(0,len(bottom)):
            bottom[i] += degreedist[j][i]

    plt.legend(prop={'size':10})
    plt.show()
