from math import *
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.sparse.csgraph import connected_components

def generateGraph(paths,pos):
    num_to_node = sorted(paths.keys())
    node_to_num = {num_to_node[i]: i for i in range(0,len(num_to_node))}

    m = csr_matrix((len(num_to_node),len(num_to_node)))
    for dst in paths:
        for src in paths[dst]:
            if int(src,16) < int(dst,16):
                # only one direction
                continue

            (dstx,dsty,dstz) = pos[dst]
            (srcx,srcy,srcz) = pos[src]
            dx = dstx-srcx
            dy = dsty-srcy
            m[node_to_num[dst],node_to_num[src]] = sqrt(dx*dx+dy*dy)

    return m

def calculateLargestConnectedComponent(paths,pos):
    num_to_node = sorted(paths.keys())
    node_to_num = {num_to_node[i]: i for i in range(0,len(num_to_node))}
    m = generateGraph(paths,pos)
    cc = connected_components(m)
    ccs = []
    for i in range(cc[0]):
        ccs.append([num_to_node[x[0]] for x in [x for x in [(x,cc[1][x]) for x in range(len(cc[1]))] if x[1] == i]])
    return max(ccs, key=lambda x: len(x))

def calculateExtendedMST(paths,pos):
    num_to_node = sorted(paths.keys())
    node_to_num = {num_to_node[i]: i for i in range(0,len(num_to_node))}

    m = generateGraph(paths,pos)

    def inMST(csr,src,dst):
        t = csr[node_to_num[dst],node_to_num[src]]
        return (t != 0.0)

    Tcsr = minimum_spanning_tree(m)
        
    # Calculate MST of other edges
    for i in range(0,2):
        for dst in paths:
            for src in paths[dst]:
                if inMST(Tcsr,src,dst):
                    m[node_to_num[dst],node_to_num[src]] = 99999

        Tcsr2 = minimum_spanning_tree(m)
        Tcsr = Tcsr+Tcsr2

    # Format result
    mst = {}

    for dst in paths:
        for src in paths[dst]:
            if not dst in mst:
                mst[dst] = {}
            mst[dst][src] = inMST(Tcsr,src,dst)

    return mst
