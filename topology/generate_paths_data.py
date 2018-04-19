#!/usr/bin/env python3

import fileinput
import argparse
import json
import re
import sys
sys.path.insert(0, '../helper')
from address_finder import *

def generate(args):
    output_power = 3 # dBm
    frequency = 2.4e9

    experiment_nodes = [address_for_node(args.site,args.node_type,x) for x in get_all_working(args.site,args.node_type)]

    total_packets = 0
    invalid_address_packets = 0
    paths_data = {}
    invalid_addresses = set()
    packets_by = {}
    i = 0
    for line in fileinput.input(args.files):
        i += 1

        m = re.search("!0x([0-9a-fA-F]+)!0x([0-9a-fA-F]+)!T!.!([0-9]+)",line)
        if m:
            dst = format_address(m.group(2))
            src = format_address(m.group(1))
            seq = int(m.group(3))

            if not src in packets_by:
                packets_by[src] = 0

            packets_by[src] += 1

        m = re.search(";[0-9]*\|traf\|.:!0x([0-9a-fA-F]+)!0x[0-9a-fA-F]+!!R!.![0-9a-fA-F]+!0x([0-9a-fA-F]+)!(-[0-9][0-9])![0-9]*$",line)
        if m:
            dst = format_address(m.group(2))
            src = format_address(m.group(1))

            if dst == src:
                print(line)
            assert(dst != src)

            rssi = int(m.group(3))
            path_loss = output_power-rssi

            total_packets += 1

            if src not in experiment_nodes:
                invalid_addresses.add(src)
                invalid_address_packets += 1
                continue
            elif dst not in experiment_nodes:
                invalid_addresses.add(dst)
                invalid_address_packets += 1
                continue

            if not dst in paths_data:
                paths_data[dst] = {}
            if not src in paths_data[dst]:
                paths_data[dst][src] = []


            paths_data[dst][src].append(path_loss)

    print(("Total %i packets, %i with invalid addresses"%(total_packets,invalid_address_packets)))
    print(invalid_addresses)
    print(packets_by)
    print(min(packets_by.values()))

    with open("paths-data-"+args.site+"-"+args.node_type+"-"+args.name+".json","w") as outfile:
        data = {'site':args.site,
                'node_type':args.node_type,
                'name':args.name,
                'experiment_nodes':experiment_nodes,
                'data':paths_data} 
        json.dump(data, outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('site')
    parser.add_argument('node_type')
    parser.add_argument('name')
    parser.add_argument('files', metavar='FILE', nargs='*',
                    help='the files to read')
    args = parser.parse_args()
    generate(args)
