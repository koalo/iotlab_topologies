from iotlabcli import rest
from iotlabcli import auth
import iotlabcli.parser.experiment
from iotlabcli import helpers
import json
from multiprocessing import Pool
import subprocess
import time
import os

NODE_FILENAME = 'nodes.json'

def resources(site,node_type,nodes,profile=None):
    experiment_list = site+","+node_type+","+("+".join([str(x) for x in nodes]))
    if profile:
        experiment_list += ",profile="+profile
    return iotlabcli.parser.experiment.exp_resources_from_str(experiment_list)

def nodes_from_string(string):
    parts = string.split("+")
    nodes = []
    for p in parts:
        if "-" in p:
            x = p.split("-")
            nodes += list(range(int(x[0]),int(x[1])+1))
        else:
            nodes.append(int(p))
    return nodes

def states(site,node_type,nodes):
    user, passwd = auth.get_user_credentials()
    api = rest.Api(user, passwd)

    resources = api.get_nodes(True,site)
    #resources = resources['items'][0][site][node_type]    Not working anymore -> REST API update 
    
    node_strings = {} 
    for node_types in resources['items'][0]['archis']:
        if node_type in node_types['archi']:
            for states in node_types['states']:
                node_strings[states['state']] = states['ids']                    
    resources = node_strings

    print(resources)

    for k in resources:
        resources[k] = nodes_from_string(resources[k])

    result = {}
    for k in resources:
        for n in resources[k]:
            if n in nodes:
                result[n] = k
    
    return result

def all_alive(site,node_type,nodes):
    state = states(site,node_type,nodes)
    for s in list(state.values()):
        if s != "Alive":
            print("The following nodes are currently not available")
            print([k_v for k_v in iter(state.items()) if k_v[1] != "Alive"])
            return False
    return True

def blocking_experiments(site,node_type,nodes):
    user, passwd = auth.get_user_credentials()
    api = rest.Api(user, passwd)

    experiments = api.get_experiments('Waiting,Running')['items']
    #experiments = api.get_experiments('Error')['items']
    experiments = [x for x in experiments if any(("%s-%i.%s.iot-lab.info"%(node_type,node,site) in x['resources']) for node in nodes)]
    
    return experiments

def flash_single_a8(args):
    (run,site,image,exp_id_value,node) = args
    user, passwd = auth.get_user_credentials()
    api = rest.Api(user, passwd)

    logfile = os.path.join(run['logdir'],run['name']+"_flash_"+str(node)+".log")

    ssh_options = " -o ConnectTimeout=4 -o StrictHostKeyChecking=no -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null "
    redir_cmd = "ssh -t "+user+"@"+site+".iot-lab.info ssh root@node-"+str(node)+ssh_options+"'/etc/init.d/serial_redirection start'"
    cpy_cmd = "scp -oProxyCommand=\"ssh -W %h:%p "+user+"@"+site+".iot-lab.info\""+ssh_options+image+" root@node-"+str(node)+":~/firmware.elf"
    flash_cmd = "ssh -t "+user+"@"+site+".iot-lab.info ssh root@node-"+str(node)+ssh_options+"'PATH=/usr/local/bin:/usr/bin flash_a8_m3 /home/root/firmware.elf'"

    result = 0

    with open(logfile,"w") as log:
        # Try to establish ssh connection and start serial redirection
        total_timeout = 60*60
        interval = 10
        last_reset = 0
        reset_interval = 60
        for i in range(0,int(total_timeout/interval)+1):
            for cmd in [redir_cmd,cpy_cmd,flash_cmd]:
                log.write("> "+cmd+"\n")
                log.flush()
                result = subprocess.call(cmd, stdout=log, stderr=log, shell=True)
                log.flush()
                if result != 0:
                    break

            if result == 0 or i >= total_timeout/interval-1:
                break
            else:
                if i*interval > last_reset+reset_interval:
                    log.write(">>> STOP\n")
                    result = api.node_command('stop',exp_id_value,[node])
                    log.write("Result %s\n"%str(result))
                    time.sleep(6)
                    log.write(">>> START\n")
                    result = api.node_command('start',exp_id_value,[node])
                    log.write("Result %s\n"%str(result))
                    log.flush()

                    last_reset = i*interval
                    reset_interval *= 2 # exponential increase
                time.sleep(interval)

    if result == 0:
        os.remove(logfile)

    return result

def flash(run,site,node_type,image,exp_id,nodes):
    if node_type == 'm3':
        user, passwd = auth.get_user_credentials()
        api = rest.Api(user, passwd)

        # Flash nodes
        files = helpers.FilesDict()
        files.add_firmware(image)
        files[NODE_FILENAME] = json.dumps(nodes)

        result = api.node_update(exp_id.value,files)
        print(result)
        print("Nodes "+",".join(nodes)+" flashed ")
        return True
    elif node_type == 'a8':
        p = Pool(len(nodes))
        results = p.map(flash_single_a8,[(run,site,image,exp_id.value,node) for node in nodes])
        allok = all(r == 0 for r in results)
        if allok:
            print("All nodes flash successfully")
        else:
            print("Flashing failed for ", end=' ')
            print([nodes[x] for x in [i for i in range(0,len(results)) if results[i] != 0]])
        return allok
    else:
        assert(false);

    
if __name__ == "__main__":
    #print all_alive("grenoble","m3",[150,124])
    #print blocking_experiments("grenoble","m3",[150,124])
    print(flash("saclay","a8","~/cometos/examples/hardware/dsme/bin/A8_M3/Device.elf",0,[6]))
