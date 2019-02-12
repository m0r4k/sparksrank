# !/bin/python3

import subprocess
import json
from pathlib import Path
import time
import os
import copy

coin_cli: str = 'sparks-cli'
cache_time_min: float = 10


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def cli_cmd(cmd: str, jsonify: bool = True) -> str:
    cli_output: str = subprocess.check_output(coin_cli + ' ' + cmd, shell=True).decode("utf-8")

    if jsonify:
        cli_output: str = json.loads(cli_output)

    return cli_output


def calc_file_age(filename: str) -> int:
    exists = Path(filename)

    if exists.is_file():
        age = time.time() - os.path.getmtime(filename)
    else:
        age = 0

    # returns age in minutes
    return age / 60


def write_cache(text: str, filename: str) -> bool:
    file_age = calc_file_age(filename)

    if file_age > cache_time_min or file_age == 0:
        Path(filename).write_text(text)

    return True


def write_mn_cache(text: str, filename: str) -> bool:
    file_age = calc_file_age(filename)

    if file_age > cache_time_min or file_age == 0:
        iter_num: int = 0
        output = ""
        iter_string = ""
        for i in text.split('\"masternode\"'):
            if iter_num != 0:
                iter_string = '\"' + str(iter_num) + '\"'

            output = "".join([output, iter_string + ' ' + i])
            iter_num = iter_num + 1

        Path(filename).write_text(output)
    return True


def sortMnCache(file: dict, conf: dict) -> dict:
    txid: dict = []
    for i in conf:
        txid.append(conf[i]['txHash'] + "-" + conf[i]['outputIndex'])

    output = file
    for i in output.copy():
        if i not in txid:
            output.pop(i)

    return output


def sortEnabled(file: dict) -> int:
    for i in file.copy():
        if file[i]['status'] not in ["ENABLED", "SENTINEL_PING_EXPIRED"]:
            file.pop(i)
    return len(file)


def buildOutput() -> dict:
    output_obj = copy.deepcopy(conf_obj)
    sort_obj = {}
    for i in output_obj:
        consensus_txid = output_obj[i]['txHash'] + '-' + output_obj[i]['outputIndex']
        if consensus_txid in rank_obj:
            output_obj[i]['rank'] = rank_obj[consensus_txid]
            output_obj[i]['maxEnabled'] = len(list_obj)
            output_obj[i]['protocol'] = list_obj[consensus_txid]['protocol']
            output_obj[i]['sentinelversion'] = list_obj[consensus_txid]['sentinelversion']

    for i in output_obj:
        sort_obj[output_obj[i]['rank']] = output_obj[i]

    output_obj = {}
    for i in sorted(sort_obj):
        output_obj[i] = sort_obj[i]

    return output_obj


def printOutput(list: dict = {}):
    print('{:<25s} {:<25s} {:4s} {:1s} {:>4s} {:>6s} {:1s} {:>20s} {:>1s} {:<18s} {:1s} {:<30s}'.format(
        bcolors.BOLD + bcolors.HEADER +
        'Masternode' + bcolors.ENDC,
        bcolors.BOLD + 'IP-Address' + bcolors.ENDC,
        'MAX',
        '|',
        'POS',
        'PERC',
        '%',
        bcolors.OKGREEN + 'Proto' + bcolors.ENDC,
        '|',
        bcolors.OKGREEN + 'sentinel' + bcolors.ENDC,
        '|',
        bcolors.OKBLUE + 'status' + bcolors.ENDC
    ))
    print('{:=<115}'.format(bcolors.HEADER + '' + bcolors.ENDC))

    ## CREATE LINES
    output = buildOutput()
    for line in output:
        pcol = scol = stcol = bcolors.FAIL

        if output[line]['protocol'] >= 70210:
            pcol = bcolors.OKGREEN

        if output[line]['sentinelversion'] == '1.2.0':
            scol = bcolors.OKGREEN

        if output[line]['status'] == 'ENABLED':
            stcol = bcolors.OKGREEN

        position = output[line]['rank'] / output[line]['maxEnabled'] * 100

        print('{:<25s} {:<25s} {:4d} {:1s} {:>4d} {:>6d} {:1s}{:>20s} {:>2s} {:<18s} {:1s} {:30s}'.format(
            bcolors.BOLD + bcolors.OKBLUE + output[line]['alias'] + bcolors.ENDC,
            bcolors.BOLD + output[line]['address'].split(':')[0] + bcolors.ENDC,
            output[line]['maxEnabled'],
            '|',
            output[line]['rank'],
            round(position),
            '%',
            pcol + str(output[line]['protocol']) + bcolors.ENDC,
            '|',
            scol + str(output[line]['sentinelversion']) + bcolors.ENDC,
            '|',
            stcol + str(output[line]['status']) + bcolors.ENDC
        ))


#### Write the FILES ####
write_cache(cli_cmd('masternode list', False), './mn_list.json')
write_cache(cli_cmd('masternode list rank', False), './mn_rank.json')
write_mn_cache(cli_cmd('masternode list-conf', False), "./mn_conf.json")

#### Open the FILES ####
list_obj: dict = json.loads(open('mn_list.json', 'r').read())
rank_obj: dict = json.loads(open('mn_rank.json', 'r').read())
conf_obj: dict = json.loads(open('mn_conf.json', 'r').read())

printOutput()
