#!/usr/bin/env python3
import networkx as nx
import sys
import os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))),'topology'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))),'helper'))
import pygraphviz as pgv
import load
import argparse
import pulp
import errno

NODE_TYPE = 'm3'
CACHE_FOLDER = os.path.join(os.path.dirname(__file__),'cache')
RESULT_FOLDER = os.path.join(os.path.dirname(__file__),'results')

def process(site,name,G,bound,degree):
    res = nx.Graph(undirected=True)

    for (u,v,d) in G.edges(data=True):
        if d['weight'] <= bound:
            res.add_edge(u,v)

    count = 0

    K = res.to_undirected()
    prob = pulp.LpProblem("NodeReduction",pulp.LpMaximize)
    x = {n: pulp.LpVariable("Node_"+str(n),0,1,pulp.LpInteger) for n in K.nodes()}

    prob += sum(x.values()) # maximize objective function

    for n in K.nodes():
        neighbours = [x[v] for (u,v) in K.edges([n])]
        prob += sum(neighbours) <= degree+len(G.nodes())*(1-x[n])
        prob += sum(neighbours) >= degree*x[n]

    prob.solve()

    for n in K.nodes():
        if not x[n].varValue == 1:
            res.remove_node(n)
    count = len(res.nodes())

    plotname = os.path.join(RESULT_FOLDER,'%s-%s-degree-%i-bound-%02i.png'%(site,name,degree,bound))

    dot = pgv.AGraph(splines=True,directed=False)
    dot.graph_attr['rankdir'] = 'BT'
    for a,b in res.edges():
        dot.add_edge(b,a,label="%.1f"%G[b][a]['weight']) # invert, because res was inverted

    print("")
    print("Topology with %i nodes for bound %i:"%(count,bound))
    print([n for n in res.nodes()])
    print("Graph plot in %s"%plotname)

    dot.write(plotname.replace("png","dot"))
    dot.draw(plotname,prog='fdp')

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
    parser.add_argument('bound',type=int,help='Bound')
    parser.add_argument('--degree','-d',default=3,type=int,help='Degree (default 3)')
    parser.add_argument('--reload','-r',action='store_true', help='reload cached graph (after new channel measurement).')
    args = parser.parse_args()

    # Create folders if not exist
    mkdirp(RESULT_FOLDER)
    mkdirp(CACHE_FOLDER)

    fname = os.path.join(CACHE_FOLDER,args.site+'-'+args.name+'.pick')
    G = load.load_graph(args.site,args.name,fname,args.reload)
    process(args.site,args.name,G,args.bound,args.degree)

