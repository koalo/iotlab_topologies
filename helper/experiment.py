from multiprocessing import Process, Value
import time
import os
import iotlabcli.parser.node
import argparse

import iotlabcli.experiment
from iotlabcli import helpers
from iotlabcli import rest
from iotlabcli import auth
from iotlabcli import profile
from iotlabcli.parser import common, help_msgs

from measurement import *
from sniffer import *
from helpers import *

EXPERIMENT_NAME = "experiment" 
PROFILE_NAME = "experimentprofile"

def submit_experiment(resources, max_duration, exp_id_result, start_time=None, power_average=None):
    print(resources)
    print("Started")

    user, passwd = auth.get_user_credentials()
    api = rest.Api(user, passwd)

    if power_average:
        m3_prof = profile.ProfileM3(PROFILE_NAME, 'dc')
        m3_prof.set_consumption(140, power_average, True, True, True)
        m3_prof.set_radio('sniffer',[20])
        api.add_profile(PROFILE_NAME,m3_prof)

    result = iotlabcli.experiment.submit_experiment(api, EXPERIMENT_NAME, max_duration, [resources], start_time=start_time)
    print(result)
    
    exp_id_result.value = result['id']
    print(exp_id_result.value)

    print("Waiting")   
    result = iotlabcli.experiment.wait_experiment(api, exp_id_result.value)
    print(result)

def stop_all(site,node_type,nodes):
    user, passwd = auth.get_user_credentials()
    api = rest.Api(user, passwd)

    blocking = blocking_experiments(site,node_type,nodes)

    for exp in blocking:
        eid = exp['id']
        print("Stopping "+str(eid))
        result = api.stop_experiment(eid)
        print(result)
        
        print("Waiting for stopping "+str(eid))
        result = iotlabcli.experiment.wait_experiment(api, eid, states = 'Terminated,Error')
        print(result)

def finish(exp_id):
    print("Finish experiments")
    user, passwd = auth.get_user_credentials()
    api = rest.Api(user, passwd)

    result = iotlabcli.experiment.stop_experiment(api, exp_id.value)
    print(result)

def initialize(site, node_type, experiment_nodes, max_duration, logdir, sniffer_nodes = [], start_time=None, power_average=None, force=None, wait=None):
    if not os.path.exists(logdir) or not os.path.isdir(logdir):
        print("%s does not exist or is not a directory"%logdir)
        return None

    # Parse arguments
    if force is None or wait is None:
        parser = argparse.ArgumentParser()
        parser.add_argument('--force','-f', action='store_true', help='Stop blocking experiments before submitting the new one')
        parser.add_argument('--wait','-w',  action='store_true', help='Wait if experiment is blocked by other experiments or unavailable nodes')
        args = parser.parse_args()
        force = args.force
        wait = args.wait

    # Stop all blocking experiments
    all_nodes = experiment_nodes + sniffer_nodes
    if force:
        stop_all(site,node_type,all_nodes)

    # Check if available
    blocking = blocking_experiments(site,node_type,all_nodes)
    if len(blocking) > 0:
        print("The following experiments block the new experiment")
        print(blocking)
        if not wait:
            return None

    if not all_alive(site,node_type,all_nodes):
        if not wait:
            return None

    exp_id = Value('i',0) # will be filled by submit_experiment

    if power_average:
        total_resources = resources(site,node_type,experiment_nodes+sniffer_nodes,PROFILE_NAME)
    else:
        total_resources = resources(site,node_type,experiment_nodes+sniffer_nodes)
    experiment_resources = resources(site,node_type,experiment_nodes)

    print(total_resources)

    # Initialize the experiments
    labaction = Process(target=submit_experiment, args=(total_resources,max_duration,exp_id,start_time,power_average))
    labaction.start()

    return exp_id,labaction,experiment_resources

def run_all(site, node_type, experiment_nodes, runs, image, max_duration, logdir, sniffer_nodes = [], start_time=None, timeout_minutes=15, power_average=None, force=None, wait=None):
    result = initialize(site, node_type, experiment_nodes, max_duration, logdir, sniffer_nodes, start_time, power_average, force, wait)
    if result is None:
        return
    else:
        exp_id,labaction,experiment_resources = result

    # Assert that names are unique
    assert(len(runs) == len(set([x['name'] for x in runs])))

    sniffer_initialized = False
        
    for run in runs:
        run['image'] = image
        run['logdir'] = logdir
        
        # Start the build
        build_successful = Value('b',False)
        build = Process(target=building, args=(run,build_successful))
        build.start()

        # Wait for labaction and build before proceeding
        labaction.join()
        build.join()

        if not sniffer_initialized:
            init_sniffer(run,site,node_type,sniffer_nodes,exp_id)
            sniffer_initialized = True

        if not build_successful.value:
            print("Build not successful")
            finish(exp_id)
            return False

        # Flash nodes
        success = flash(run,site,node_type,run['image'],exp_id,experiment_resources['nodes'])
        if not success:
            print("Flashing nodes was not successful")
            finish(exp_id)
            return False

        # Run experiment
        labaction = Process(target=run_measurement, args=(run,node_type,exp_id,experiment_resources['nodes'],timeout_minutes,power_average))
        labaction.start()

    # Wait for last labaction then finish
    labaction.join()
    finish(exp_id)
    return True

