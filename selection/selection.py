#!/usr/bin/env python3
import json
import numpy as np
import math
import networkx as nx
from collections import deque
import sys
import os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))),'topology'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))),'helper'))
from address_finder import *
import helpers
import pygraphviz as pgv
import matplotlib.pyplot as plt
import pandas as pd
import load
import argparse
from pulp import *
import time
import errno
from multiprocessing import Pool
import multiprocessing

NODE_TYPE = 'm3'
CACHE_FOLDER = os.path.join(os.path.dirname(__file__),'cache')
RESULT_FOLDER = os.path.join(os.path.dirname(__file__),'results')

def kappa_fun(kind,depth):
    if kind == 'tree':
        return depth+1
    elif kind == 'line':
        return 1
    else:
        assert False

def load_graph(site,name,reload):
    fname = os.path.join(CACHE_FOLDER,site+'-'+name+'.pick')
    if not os.path.isfile(fname) or reload:
        print("Building graph cache")
        load.load_graph(site,name,fname)
    G = nx.read_gpickle(fname)
    print("Graph loaded")
    return G

def process(G,bound,root,kappa='tree',c=None,reduction=False,margin=8):
    depths = {x: float('inf') for x in G.nodes()}
    current_level = deque([root])
    next_level = deque()

    parent = {}
    depth = 0
    res = nx.DiGraph()

    count = 0

    while True:
        for n in current_level:
            depths[n] = depth
            count += 1

            for (u,v,d) in G.edges([n],data=True):
                assert(n == u)
                if d['weight'] <= bound:
                    found_in_current_level = v in next_level
                    in_current_level = v in current_level

                    if in_current_level:
                        # v on same level
                        pass
                    elif depths[v] != float('inf'):
                        # back edge
                        res.add_edge(v,n) # other direction to enable removing leafs
                    else:
                        # forward edge
                        if not found_in_current_level:
                            # check if weak link to lower nodes exists (current level is ok!)
                            avoid = False
                            for (w,y,e) in G.edges([v],data=True):
                                assert(w == v)
                                if e['weight'] <= bound+margin:
                                    if depths[y] < depth:
                                        # avoid nodes with weak edges to lower nodes!
                                        avoid = True
                                        break

                            if not avoid:
                                next_level.append(v)
                                if reduction:
                                    parent[v] = u

        if len(next_level) >= kappa_fun(kappa,depth+1): # depth for next level, so +1
            current_level = next_level
            next_level = deque()
            depth += 1
        else:
            break

    if reduction:
        before = len(res.nodes())
        K = res.to_undirected()
        prob = LpProblem("NodeReduction",LpMinimize)
        x = {n: LpVariable("Node_"+str(n),0,1,LpInteger) for n in K.nodes()}

        prob += sum(x.values()) # minimize objective function

        for j in range(1,depth+1):
            prob += sum([v for k,v in x.items() if depths[k] == j]) >= kappa_fun(kappa,j)

        for n in K.nodes():
            if n == root:
                continue
            potential_parents = [x[v] for (u,v) in K.edges([n]) if depths[u] > depths[v]]
            prob += x[n] <= sum(potential_parents)
        
        start = time.time()
        prob.solve()
        end = time.time()

        for n in K.nodes():
            if not x[n].varValue == 1:
                res.remove_node(n)
        count = len(res.nodes())

    dat = [{'bound':bound,
            'root':root,
            'depth':depth,
            'allnodes':len(G.nodes()),
            'nodes':count}]

    if res is not None:
        if len(res.edges()) > 1:
            dat[0]['maxweight'] = max([G[u][v]['weight'] for (u,v) in res.edges()])
        else:
            dat[0]['maxweight'] = 0

    return dat,res

def procwrap(params):
    sdat = []
    for root in sorted(params['G'].nodes()):
        dat,res = process(params['G'],params['bound'],root,kappa=params['kappa'],margin=params['margin'],reduction=params['reduction'])
        sdat += dat
    print("Testing bound "+str(params['bound']))
    return sdat

def check_all(G,site,name,kappa,margin,reduction):
    p = Pool(multiprocessing.cpu_count())
    tdat = p.map(procwrap, [{'G':G,'bound':bound,'kappa':kappa,'margin':margin,'reduction':reduction} for bound in list(range(35,75))+[1000]])
    dat = []
    for t in tdat:
        dat += t

    df = pd.DataFrame(dat)
    df['kappa'] = kappa
    df['margin'] = margin
    return df

def print_topos(G,df,site,name,kappa,margin=6,reduction=True,count=10):
    df.sort_values(['depth'],inplace=True,ascending=[False])

    c = 0
    for i,r in df.iterrows():
        c += 1
        if c > count:
            break

        plotname = os.path.join(RESULT_FOLDER,'%s-%s-%02i.png'%(site,name,c))

        dat,res = process(G,r.bound,r.root,c=c,reduction=reduction,margin=margin,kappa=kappa)
        dot = pgv.AGraph(splines=True,directed=True)
        dot.graph_attr['rankdir'] = 'BT'
        for a,b in res.edges():
            dot.add_edge(b,a,label="%.1f"%G[b][a]['weight']) # invert, because res was inverted

        print("")
        rootaddr = address_for_node(site, NODE_TYPE, r.root)[2:]
        print("Topology with %i nodes, depth %i and root %i (0x%s) for bound %i:"%(r.nodes,r.depth,r.root,rootaddr,r.bound))
        print([n for n in res.nodes()])
        print("Graph plot in %s"%plotname)

        dot.draw(plotname,prog='dot')

def mkdirp(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('site')
    parser.add_argument('name')
    parser.add_argument('--margin','-m',default=8,type=int)
    parser.add_argument('--kappa','-k',default='tree',nargs='?',const='tree',choices=['line','tree'],help='choose between tree (kappa(delta) = delta+1) and line (kappa(delta) = 1). Other functions should be added in the code.')
    parser.add_argument('--no-reduction','-n',action='store_true', help='do not perform the node reduction part of the algorithm.')
    parser.add_argument('--reload','-r',action='store_true', help='reload cached graph (after new channel measurement).')
    parser.add_argument('--count','-c',type=int,default=5, help='number of topology suggestions to print out (sorted by depth).')
    parser.add_argument('--print-only','-p',action='store_true', help='only read and print from existing CSV result file.')
    args = parser.parse_args()

    # Create folders if not exist
    mkdirp(RESULT_FOLDER)
    mkdirp(CACHE_FOLDER)

    G = load_graph(args.site,args.name,args.reload)

    csvname = os.path.join(RESULT_FOLDER,args.site+"-"+args.name+'.csv')
    if not args.print_only:
        df = check_all(G,args.site,args.name,kappa=args.kappa,reduction=not args.no_reduction,margin=args.margin)
        df.to_csv(csvname)
    elif not os.path.isfile(csvname):
        print("No CSV result file to read from")
        exit(1)
    else:
        df = pd.read_csv(csvname)

    print_topos(G,df,args.site,args.name,kappa=args.kappa,reduction=not args.no_reduction,margin=args.margin,count=args.count)

