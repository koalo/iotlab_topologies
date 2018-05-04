#!/usr/bin/env python3
import json
import numpy as np
import math
import networkx as nx
from collections import deque
import sys
import os
sys.path.insert(0,os.path.dirname(__file__)+'/../topology')
sys.path.insert(0,os.path.dirname(__file__)+'/../helper')
from address_finder import *
import pygraphviz as pgv
import matplotlib.pyplot as plt
import pandas as pd

def load_graph(site,fileprefix,fname,reload):
    if not os.path.isfile(fname) or reload:
        print("Building graph cache")
        with open(os.path.dirname(__file__)+'/../topology/paths-data-'+site+'-m3-'+fileprefix+'.json','r') as f:
            data = json.load(f)
            paths_data = data['data']
            site = data['site']
            node_type = data['node_type']

        G = nx.Graph()
        for dst in paths_data:
            for src in paths_data[dst]:
                if dst in paths_data[src]: # only bidirectional links
                    ds = np.mean(paths_data[dst][src])
                    sd = np.mean(paths_data[src][dst])
                    srcn = num_for_address(node_type,src)
                    dstn = num_for_address(node_type,dst)
                    w = max(ds,sd)
                    G.add_edge(srcn,dstn,weight=w)

        nx.write_gpickle(G,fname)
    else:
        G = nx.read_gpickle(fname)
    print("Graph loaded")
    return G

