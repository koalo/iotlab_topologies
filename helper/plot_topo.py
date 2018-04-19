import pygraphviz as pgv
import warnings
import numpy as np
import subprocess

def plot_topo(graph,pos,toponame,prog='neato',directed=False,sep='auto'):
    dot = pgv.AGraph(splines=True,sep=0.1,label=toponame,directed=directed)
    scale = 1.5

    # Generate graph
    for dst in graph:
        (dstx,dsty,dstz) = pos[dst]
        dot.add_node(dst,pos="%f,%f!"%(dstx*scale,dsty*scale))
        for src in graph[dst]:
            (srcx,srcy,srcz) = pos[src]
            dot.add_node(src,pos="%f,%f!"%(srcx*scale,srcy*scale))
            dot.add_edge(dst,src,label=graph[dst][src])

    if sep == 'auto':
        warnings.filterwarnings('error')
        for sep in np.arange(10,0,-0.1):
            try:
                dot.graph_attr['sep'] = sep
                dot.write(toponame+".dot")
                dot.draw(toponame+'.pdf',prog=prog,args='-n2')
                break
            except RuntimeWarning:
                continue
    else:
        dot.graph_attr['sep'] = sep
        dot.write(toponame+".dot")
        dot.draw(toponame+'.pdf',prog=prog,args='-n2')

    subprocess.call(['convert',toponame+'.pdf',toponame+'.png'])
