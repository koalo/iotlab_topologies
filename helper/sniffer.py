import os
from helpers import *
import subprocess

#SNIFFER_PATH = os.path.join(os.environ['COMETOS_PATH'], 'examples/hardware/sniffer/M3RssiSniffer')
#SNIFFER_CMD = "cob channel_test=True sniff_channel=0 own_pan_id=121"

SNIFFER_PATH = os.path.join(os.environ['COMETOS_PATH'], 'examples/hardware/sniffer/PureSniffer')
SNIFFER_CMD = "cob platform=M3OpenNode mac_default_channel=13"

SNIFFER_IMAGE = os.path.join(SNIFFER_PATH,"bin/M3OpenNode/Device.elf")

def init_sniffer(run,site,node_type,sniffer_nodes,exp_id):
    if len(sniffer_nodes) == 0:
        return

    # Remove image first to verify later it is this file that is built
    try:
        os.remove(SNIFFER_IMAGE)
    except OSError:
        pass # not existing so no problem

    result = subprocess.call(SNIFFER_CMD, stdout=None, stderr=None, shell=True, cwd=SNIFFER_PATH)
    assert(result == 0)

    sniffer_resources = resources(site,node_type,sniffer_nodes)
    flash(run,site,node_type,SNIFFER_IMAGE,exp_id,sniffer_resources['nodes'])

