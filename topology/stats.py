import json
import numpy as np

def stats(fname):
    with open(fname,"r") as infile:
        data = json.load(infile)
        paths_data = data['data']
        site = data['site']
        node_type = data['node_type']
        name = data['name']
        experiment_nodes = data['experiment_nodes']

    paths = {}
    for dst in paths_data:
        paths[dst] = {}
        for src in paths_data[dst]:
            data = paths_data[dst][src]
            paths[dst][src] = {}
            paths[dst][src]['mean'] = np.mean(data)
            paths[dst][src]['median'] = np.median(data)
            paths[dst][src]['min'] = min(data)
            paths[dst][src]['max'] = max(data)
            paths[dst][src]['p'] = np.percentile(data,10)
            paths[dst][src]['count'] = len(data)
            maxmean = float('inf')
            if src in paths_data:
                if dst in paths_data[src]:
                    maxmean = max(paths[dst][src]['mean'], np.mean(paths_data[src][dst]))
            paths[dst][src]['maxmean'] = maxmean
    return paths

