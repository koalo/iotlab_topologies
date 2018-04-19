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
    pan_coordinator = "0xFFFF"
    max_path_loss = [float('inf')]
    tx_pwr = [15]
    intervals = [2000]
    repetitions = 4

    channels=[19]

    ccamd = [2]
    # 1 Energy above threshold
    # 2 Carrier sense only
    # 0 = 1 || 2
    # 3 = 1 && 2

    experiment_nodes = filter_own_suspected(site,node_type,experiment_nodes)

    print(("Experiment with %i nodes"%len(experiment_nodes)))
    print(experiment_nodes)

    image = {"m3":"bin/M3OpenNode/Device.elf","a8":"bin/A8_M3/Device.elf"}
    platform = {"m3":"M3OpenNode","a8":"A8_M3"}

    runs = []
    for (repetition,interval,max_path_loss,ccamd,channel) in itertools.product(list(range(0,repetitions)), intervals, max_path_loss, ccamd, channels):
        if max_path_loss == float('inf'):
            pdt_level = 0
            ed = -90
            tx_pwr = 3
            tx_pwr_lvl = 0 # 0 corresponds to 3 dBm
        elif max_path_loss == 83:
            # minimum tx power, full sensitivity
            pdt_level = 0
            ed = -90
            tx_pwr = -17
            tx_pwr_lvl = 0xF # 0xF corresponds to -17 dBm
        else:
            # currently only works for minimum transmission power and respective sensitivity
            tx_pwr = -17
            tx_pwr_lvl = 0xF # 0xF corresponds to -17 dBm
            sens = tx_pwr - max_path_loss
            assert -90 <= sens <= -48, "%i not in [-90,-48]"%sens

            if ccamd == 2: # carrier sense only
                ed = -90 # irrelevant
            else:
                ed = sens
                assert -90 <= ed <= -60, "%i not in [-90,-60]"%ed

            pdt_level = int(round((sens - (-90))/3.0+1))
            max_path_loss = tx_pwr - (-90 + 3*(pdt_level-1)) # recalculate mpl (pdt_level might be rounded)

        name = "interval_%03i_site_%s_mpl_%.0f_pwr_%s_pdt_%s_ed_%i_ccamd_%i_chan_%i_run_%i"%(interval,site,max_path_loss,tx_pwr,pdt_level,ed,ccamd,channel,repetition)
        
        pwrlvl = 15-tx_pwr_lvl # inverted in CometOS

        build_cmd = "cob "+\
                    " send_interval="+str(interval)+\
                    " mac_default_tx_power_lvl="+str(pwrlvl)+\
                    " mac_default_rx_pdt_level="+str(pdt_level)+\
                    " mac_default_cca_threshold="+str(ed)+\
                    " mac_default_cca_mode="+str(ccamd)+\
                    " mac_default_channel="+str(channel)+\
                    " platform="+platform[node_type]
        runs.append({"name": name, "build_cmd": build_cmd})


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
