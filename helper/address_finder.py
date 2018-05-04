#!/usr/bin/env python3
import json
import datetime
from functools import lru_cache
import iotlabcli.experiment
from iotlabcli import auth
from iotlabcli import rest

NODE_CACHE_FILENAME = "node_cache.json"
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
REFRESH_PERIOD_HOURS = 1

corrections = {
        "a8-9.saclay.iot-lab.info": {"in_cache": "", "correct": "b252"},
        "a8-18.saclay.iot-lab.info": {"in_cache": "", "correct": "8665"},
        "a8-20.saclay.iot-lab.info": {"in_cache": "", "correct": "a567"},
        "a8-29.saclay.iot-lab.info": {"in_cache": "", "correct": "b152"},
        "a8-34.saclay.iot-lab.info": {"in_cache": "", "correct": "9553"},
        "a8-38.saclay.iot-lab.info": {"in_cache": "", "correct": "9254"},
        "a8-118.saclay.iot-lab.info": {"in_cache": "", "correct": "a167"},
        "a8-134.saclay.iot-lab.info": {"in_cache": "", "correct": "9554"},
        "a8-158.saclay.iot-lab.info": {"in_cache": "", "correct": "a766"}
}

own_suspected = {
    "a8": {
        #"grenoble": [111,140,158,164,172,186,28,6,72],
        #"paris": [10,21,31,57],
        #"saclay": [101,113,119,11,126,131,135,136,146,158,171,43,48,4,50,53,54,68,77,81,84,8,91],
        #"lyon": [3],
        #"strasbourg": [8]
    },
    "m3": {
        "grenoble": [158,194,206,291,353],
        "lille": [72,74,133,175,188,189],
        "strasbourg": [25]
    }
}

def filter_own_suspected(site,node_type,nodes):
    if site not in list(own_suspected[node_type].keys()):
        return nodes
    else:
        return [x for x in nodes if x not in own_suspected[node_type][site]]

def format_address(v):
    if isinstance(v,str):
        v = v.replace("0x","")
        v = v.strip()
        if v == 'uuuu':
            v = 0
        else:
            v = int("0"+v,16) # "0"+ for empty strings
    assert(isinstance(v,int))
    return "0x%04x"%v

corrections_inv = {format_address(d['correct']): addr for addr, d in corrections.items()}

def data_for_node(site, node_type, node):
    info = get_info_cached()
    addr = node_type+"-"+str(node)+"."+site+".iot-lab.info"
    lst = list(filter(lambda x: x['network_address'] == addr, info['items']))
    if len(lst) == 1:
        return lst[0]
    else:
        print(node_type,node,site)
        print(addr, lst)
        assert(False)

def address_for_node(site, node_type, node):
    node = data_for_node(site,node_type,node)
    addr = node_type+"-"+str(node)+"."+site+".iot-lab.info"
    uid = node['uid']
    if addr in corrections:
        assert(corrections[addr]["in_cache"].strip() == uid.strip())
        uid = corrections[addr]["correct"]
    if uid.strip() == "":
        uid = 0
    return format_address(uid)

def data_for_address(node_type, uid):
    info = get_info_cached()
    if uid in list(corrections_inv.keys()):
        node = [x for x in info['items'] if corrections_inv[uid] == x['network_address']]
    else: 
        node = [x for x in info['items'] if format_address(x['uid']) == format_address(uid) and node_type in x['network_address']]
    return node[0]

def node_for_address(node_type, uid):
    return data_for_address(node_type,uid)['network_address']

def num_for_address(node_type, uid):
    url = node_for_address(node_type,uid)
    return int(url.split(".")[0].split("-")[1])

@lru_cache(maxsize=1)
def get_info_cached():
    now = datetime.datetime.now()
    data = {}
    try:
        with open(NODE_CACHE_FILENAME) as f:
            data = json.load(f)

        cache_time = datetime.datetime.strptime(data["time"], TIME_FORMAT)
        if now - cache_time > datetime.timedelta(hours=REFRESH_PERIOD_HOURS):
            raise Exception("Too old")
    except:
        print("Reload node data")
        try:
            user, passwd = auth.get_user_credentials()
            api = rest.Api(user, passwd)
            newdata = iotlabcli.experiment.info_experiment(api)
            newdata["time"] = now.strftime(TIME_FORMAT)

            with open(NODE_CACHE_FILENAME, 'w') as outfile:
                json.dump(newdata, outfile, sort_keys=True,
                      indent=4, separators=(',', ': '))

            data = newdata
        except:
            pass # use cached data anyway
    print("Node data loaded")

    return data

def get_all_working(site,node_type):
    info = get_info_cached()
    nodes = [x for x in info['items'] if node_type in x['network_address'] and site == x['site'] and x['state'] in ['Busy','Alive'] and x['mobile'] == 0]
    return [int(x['network_address'].split(".")[0].split("-")[1]) for x in nodes]

def get_all_available(site,node_type):
    info = get_info_cached()
    nodes = [x for x in info['items'] if node_type in x['network_address'] and site == x['site'] and x['state'] in ['Alive'] and x['mobile'] == 0]
    return [int(x['network_address'].split(".")[0].split("-")[1]) for x in nodes]

if __name__ == "__main__":
    #print address_for_node("grenoble","m3",150)
    print(get_all_working("grenoble","m3"))
