#!/usr/bin/env python3

import fileinput
import argparse
import re
import sys
sys.path.insert(0, '../helper')
from address_finder import *
import collections

def test_ids(args):
    print("------------------------")
    print(args.site+" "+args.node_type)
    nodes = {}
    for line in fileinput.input(args.files):
        m = re.search(";(.*);.*!0x[0-9a-fA-F]+!0x.+!!R!.!.+!(0x[0-9a-fA-F]+)!-[0-9][0-9]",line)
        if m:
            node = int(m.group(1).split("-")[-1])
            own = int(m.group(2),0)
            #print node,own
            if node in nodes:
                if own != nodes[node]:
                    print(line)
            else:
                nodes[node] = own

    correct = 0
    total = 0
    for k,v in nodes.items():
        a = address_for_node(args.site,args.node_type,k)
        try:
            cached = int(a,0)
        except ValueError:
            print(a)
            cached = -1

        total += 1
        if v != cached:
            print("%i 0x%x 0x%x"%(k,v,cached))
        else:
            correct += 1

    print("%i/%i ids are correct"%(correct,total))

    print([item for item, count in list(collections.Counter(list(nodes.values())).items()) if count > 1])

    # Find out missing nodes
    allnodes = get_all_working(args.site,args.node_type)
    suspects = [k for k in allnodes if not k in nodes.keys()]
    if len(suspects) > 0:
        print("The following nodes assumed working at "+args.site+" did not show up")
        print(suspects)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('site')
    parser.add_argument('node_type')
    parser.add_argument('files', metavar='FILE', nargs='*',
                    help='the files to read')
    args = parser.parse_args()
    test_ids(args)
