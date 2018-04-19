#!/usr/bin/env python3

from address_finder import *

def position_for_address(node_type, uid):
    node = data_for_address(node_type,uid)
    return (float(node['x']),float(node['y']),float(node['z']))

def position_for_node(site, node_type, node):
    noded = data_for_node(site,node_type,node)
    return (float(noded['x']),float(noded['y']),float(noded['z']))

def position_string_for_node(site,node_type,node):
    scale = 1000
    uid = address_for_node(site,node_type,node)
    p = position_for_node(site,node_type,node)
    for x in p:
        assert abs(x*scale-round(x*scale)) < 0.001, "scale %i is not sufficient for %f, %f != %i"%(scale,x,x*scale,round(x*scale))
    return "%s,%i,%i,%i"%(uid,p[0]*scale,p[1]*scale,p[2]*scale)

def get_positions_string(site,node_type,nodes):
    positions = [position_string_for_node(site,node_type,node) for node in nodes]
    return ":".join(positions),len(positions)

if __name__ == "__main__":
    site = "grenoble"
    node_type = "m3"
    nodes = get_all_working(site,node_type)
    (positions,num) = get_positions_string(site,node_type,nodes)
    print(num, positions)
