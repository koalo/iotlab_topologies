import os
import subprocess
import datetime
import time
import re

import iotlabcli.experiment
from iotlabcli import helpers
from iotlabcli import rest
from iotlabcli import auth
from iotlabcli.parser import common, help_msgs
import iotlabcli.parser.experiment
import socket
import signal

SHUTDOWN_LINE = "--- experiment finished ---"
DEBUGGER = False

def run_with_timeout(timeout, default, f, *args, **kwargs):
    if not timeout:
        return f(*args, **kwargs)
    try:
        def handler():
            raise Exception()
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout)
        result = f(*args, **kwargs)
        signal.alarm(0)
        return result
    except Exception:
        return default

def building(run,build_successful):
    # Remove image first to verify later it is this file that is built
    try:
        os.remove(run['image'])
    except OSError:
        pass # not existing so no problem

    # Build and write log
    with open(os.path.join(run['logdir'],run['name']+"_build.log"), "w") as f:
        print("Building "+run['name']+" ("+run['build_cmd']+")")
        f.write("> "+run['build_cmd'])
        f.flush()
        result = subprocess.call(run['build_cmd'], stdout=f, stderr=f, shell=True)
        f.flush()
        f.write("Return value: "+str(result))

    # Verify image now exists 
    if result == 0 and os.path.isfile(run['image']):
        build_successful.value = True
    else:
        build_successful.value = False

def ssh_cmd(cmd,user,site):
    if socket.gethostname() != site:
        cmd = "ssh %s@%s.iot-lab.info \"%s\""%(user,site,cmd)

    return cmd

def run_measurement(run,node_type,exp_id,nodes,timeout_minutes,power_average):
    user, passwd = auth.get_user_credentials()
    api = rest.Api(user, passwd)
    site = nodes[0].split('.')[1]

    # Clean power consumption measurement
    if power_average:
        cmd = ssh_cmd("truncate --size 0 ~/.iot-lab/%i/consumption/*.oml"%exp_id.value,user,site)
        subprocess.check_call(cmd,shell=True)

    # Prepare serial_aggregator
    cmd = ssh_cmd("serial_aggregator --with-a8 -i %i"%exp_id.value,user,site)
    print(cmd)
    serial = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

    # Start
    if not DEBUGGER:
        if node_type == "m3":
            result = api.node_command('reset',exp_id.value,nodes)
            print(result)
    else:
        result = api.node_command('debug-start',exp_id.value,nodes)
        print(result)
    print("Nodes started "+run['name'])

    start = datetime.datetime.now()

    # Handle serial output
    lastline = ""
    with open(os.path.join(run['logdir'],run['name']+"_run.log"), "w") as f:
        i = 0
        while True:
            line = run_with_timeout(1, None, serial.stdout.readline)
            if line is not None:
                i = i+1
                if i % 50 == 0:
                    print(".",end='',flush=True)
                line = line.decode()
                if line == "":
                    break
                f.write(line)
                f.flush()
                lastline = line
                if SHUTDOWN_LINE in line and not DEBUGGER:
                    break

            if datetime.datetime.now()-start > datetime.timedelta(minutes=timeout_minutes) and not DEBUGGER:
                break

    print('\n',end='')

    # Get power consumption results
    if power_average:
        # Get timestamp of last log line
        m = re.search("([0-9]*)\.([0-9]*);",lastline)
        assert(m)
        time_s = m.group(1)
        print("Last timestamp ",time_s)

        # Repeatedly read consumption files until the timestamp from
        # these exceed the one of the log.
        print("Waiting for cached consumption results ",end='')
        while True:
            print(",",end='',flush=True)
            cmd = ssh_cmd("ls ~/.iot-lab/%i/consumption/*.oml"%exp_id.value,user,site)
            files = subprocess.check_output(cmd,shell=True).splitlines()
            print(".",end='',flush=True)

            waiting_required = False
            for f in files:
                f = f.decode()
                m = re.search("m3-([0-9]*).oml",f)
                if not m:
                    continue

                node = m.group(1)
                print(">",end='',flush=True)
                cmd = ssh_cmd("cat "+f+" | gzip",user,site)
                output = subprocess.check_output(cmd+" | gunzip",shell=True)
                print("<",end='',flush=True)
                with open(os.path.join(run['logdir'],run['name']+"_power_"+m.group(1)+".csv"),"w") as oml:
                    oml.write("time,node,power,voltage,current\n")
                    breaked = False
                    for l in output.splitlines():
                        l = l.decode()
                        m = re.search("[0-9.]*\t[0-9]*\t[0-9]*\t([0-9]*)\t([0-9]*)\t([0-9.]*)\t([0-9.]*)\t([0-9.]*)",l)
                        if m:
                            oml.write("%s.%s,%s,%s,%s,%s\n"%(m.group(1),
                                m.group(2),node, m.group(3),
                                m.group(4),m.group(5)))
                            if int(time_s) < int(m.group(1)):
                                breaked = True
                                break
                    if not breaked:
                        waiting_required = True
            if not waiting_required:
                break
            time.sleep(10)
        print('\n', end=' ')

        

