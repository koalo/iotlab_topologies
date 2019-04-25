#!/usr/bin/env python3

import sys
sys.path.insert(0, '../helper')

import experiment
import experiment_dirs
from address_finder import *
from positions import *
import itertools
from helpers import *
import argparse

node_type = "m3"

def run_experiment(site,force,wait,exclude_busy):
    if exclude_busy:
        experiment_nodes = get_all_available(site,node_type)
    else:
        experiment_nodes = get_all_working(site,node_type)

    sniffer_nodes = []
    repetitions = 4

    experiment_nodes = filter_own_suspected(site,node_type,experiment_nodes)

    print(("Experiment with %i nodes"%len(experiment_nodes)))
    print(experiment_nodes)

    image = {"m3":"bin/M3OpenNode/Device.elf","a8":"bin/A8_M3/Device.elf"}
    platform = {"m3":"M3OpenNode","a8":"A8_M3"}

    runs = []
    for repetition in range(0,repetitions):
        name = "site_%s_run_%i"%(site,repetition)
        
        runs.append({"name": name, "build_cmd": "rm -r bin; cp -r precompiled bin"})


    print(runs)

    max_duration = 60*2

    logdir = experiment_dirs.generate_new("logs")
    start_time = None
    #start_time = (datetime.datetime.now()+datetime.timedelta(hours=5)).strftime("%s")
    experiment.run_all(site,node_type,experiment_nodes,runs,image[node_type],max_duration,logdir,sniffer_nodes,start_time=start_time,force=force,wait=wait)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('site',choices=['strasbourg','grenoble','saclay','lille','paris','lyon'],help='IoT-LAB site for the experiment')
    parser.add_argument('--force','-f', action='store_true', help='stop blocking experiments before submitting the new one')
    parser.add_argument('--wait','-w',  action='store_true', help='wait if experiment is blocked by other experiments or unavailable nodes')
    parser.add_argument('--exclude-busy','-x',  action='store_true', help='exclude nodes that are currently busy')
    args = parser.parse_args()

    run_experiment(args.site,args.force,args.wait,args.exclude_busy)
