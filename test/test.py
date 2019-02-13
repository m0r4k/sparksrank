#!/usr/bin/env python

import json
import subprocess
import sys
import time
import datetime

sys.path.insert(0, '.')

coin_cli = "sparks-cli"

def cliCmd(cmd, jsonify=True):

    try:
        cli_output = subprocess.check_output(coin_cli + ' ' + cmd, shell=True).decode("utf-8")

        if jsonify:
            cli_output = json.loads(cli_output)

        return cli_output
    except subprocess.CalledProcessError:
        quit()


mns = cliCmd('masternode list full', True)

now = int(datetime.datetime.utcnow().strftime("%s"))
mn_queue=[]
for line in mns:
    mnstat = mns[line].split()

    if mnstat[0] == 'ENABLED' or mnstat[0] == 'SENTINEL_PING_EXPIRED':
        # if last paid time == 0
        if int(mnstat[5]) == 0:
            # use active seconds
            mnstat.append(int(mnstat[4]))
        else:
            # now minus last paid
            delta = now - int(mnstat[5])
            # if > active seconds, use active seconds
            if delta >= int(mnstat[4]):
                mnstat.append(int(mnstat[4]))
            # use active seconds
            else:
                mnstat.append(delta)
        mn_queue.append(mnstat)

mn_queue = sorted(mn_queue, key=lambda x: x[8])


n=1
for line in mn_queue:
    line.append(n)
    line.append(len(mn_queue))
    if line[7] == "80.211.45.37:8890":
        print(line)

    n=n+1



print(mn_queue)