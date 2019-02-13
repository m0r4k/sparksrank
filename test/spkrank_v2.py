#!/bin/python3.5

import subprocess
import json
from pathlib import Path
import time
import os
import datetime
from collections import OrderedDict
import operator

coin_cli = 'sparks-cli'
cache_time_min = 2
enabled_mn = 0


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def cliCmd(cmd, jsonify=True):
    try:
        cli_output = subprocess.check_output(coin_cli + ' ' + cmd, shell=True).decode("utf-8")

        if jsonify:
            cli_output = json.loads(cli_output, object_pairs_hook=OrderedDict)

        return cli_output
    except subprocess.CalledProcessError:
        quit()


def fileAge(filename):
    exists = Path(filename)

    if exists.is_file():
        age = time.time() - os.path.getmtime(filename)
    else:
        age = 0

    # returns age in minutes
    return age / 60


def writeCache(text, filename):
    file_age = fileAge(filename)

    if file_age > cache_time_min or file_age == 0:
        Path(filename).write_text(text)


def writeMnCache(text, filename, output=False):
    file_age = fileAge(filename)

    if file_age > cache_time_min or file_age == 0:
        iter_num = 0
        output = ""
        iter_string = ""
        for i in text.split('\"masternode\"'):
            if iter_num != 0:
                iter_string = '\"' + str(iter_num) + '\"'

            output = "".join([output, iter_string + ' ' + i])
            iter_num = iter_num + 1

        Path(filename).write_text(output)
        if output:
            return json.loads(output, object_pairs_hook=OrderedDict)


def writeMnOutput(conf_dic, list_dic, rank_dic, filename=False):
    output_dic = dict()
    index = {}
    ip_list = {}
    mn_max_rank = len(rank_dic)
    rank_ordered = []

    for i in conf_dic:
        txid = conf_dic[i]['txHash']+'-'+conf_dic[i]['outputIndex']
        ip_list[txid] = conf_dic[i]['address']

    for i in list_dic:
        status = list_dic[i]['status']
        lastpaidtime = list_dic[i]['lastpaidtime']
        activeseconds = list_dic[i]['activeseconds']
        if status == "ENABLED" or status == "SENTINEL_PING_EXPIRED":
            index[i] = rankCalc(lastpaidtime, activeseconds)
        if i in ip_list:
            index[i] = rankCalc(lastpaidtime, activeseconds)

    #sort the index position by rankCalculation
    sorted_index = sorted(index.items(), key=lambda kv: kv[1], reverse=True)

    #build a list of txids to get the index number
    sorted_list = []
    for i in sorted_index:
        sorted_list.append(i[0])

    #write the index position back to index dict
    for i in sorted_list:
        index[i] = sorted_list.index(i)


    if filename:
        file_age = fileAge(filename)

        if file_age > cache_time_min or file_age == 0:
            for i in conf_dic:
                col_txid = conf_dic[i]['txHash'] + '-' + conf_dic[i]['outputIndex']

                ## fill rank with 0
                if list_dic != {}:
                    output_dic[index[col_txid]] = list_dic[col_txid]
                    filler = output_dic[index[col_txid]]
                    lastpaidtime = list_dic[col_txid]['lastpaidtime']
                    activeseconds = list_dic[col_txid]['activeseconds']
                    filler['rank'] = 0
                    filler['max_rank'] = 0
                    filler['alias'] = 'empty'
                    filler['mn_rank'] = 0
                    filler['mn_max_rank'] = 0
                    filler['rank_pos'] = rankCalc(lastpaidtime, activeseconds)

                #tmp_dic = cliCmd('masternode list json ')
                if list_dic != {} and col_txid in list_dic:
                    output_dic[index[col_txid]]['rank'] = index[col_txid]
                    output_dic[index[col_txid]]['max_rank'] = enabled_mn
                    output_dic[index[col_txid]]['alias'] = conf_dic[i]['alias']

                if rank_dic != {} and col_txid in rank_dic:
                    output_dic[index[col_txid]]['mn_rank'] = rank_dic[col_txid]
                    output_dic[index[col_txid]]['mn_max_rank'] = mn_max_rank

            rank_output_dic = {}
            for i in output_dic:
                new_id = output_dic[i]['rank_pos']
                rank_output_dic[new_id] = output_dic[i]

            Path(filename).write_text(json.dumps(rank_output_dic, sort_keys=True, indent=4, ensure_ascii=False))



def checkMnSync():
    check = cliCmd('mnsync status')

    if not check['IsSynced']:
        print('you need to wait till mn is synced')
        quit()


def readEnabled(mn_list):
    export_list = {}

    now = int(datetime.datetime.utcnow().strftime("%s"))
    for i in mn_list:
        status = mn_list[i]['status']
        if status == 'ENABLED' or status == 'SENTINEL_PING_EXPIRED':
            export_list[i] = mn_list[i]
    return len(export_list)


def rankCalc(lastpaidtime, activeseconds):

    now = int(datetime.datetime.now().strftime("%s"))
    if int(lastpaidtime) == 0:
        rank = activeseconds
    else:
        delta = now - lastpaidtime
        if delta >= int(activeseconds):
            rank = activeseconds
        else:
            rank = delta
    return rank


def timeCalc(time):
    if time > 0:
        day = time // (24 * 3600)
        time = time % (24 * 3600)
        hour = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        seconds = time
        return str(str(day).zfill(2)+'d '+str(hour).zfill(2)+':'+str(minutes).zfill(2))
    else:
        return str('00d 00:00')


def printOutput(output):
    now = int(datetime.datetime.now().strftime("%s"))

    # BEGIN
    print('{:-<153}'.format(bcolors.HEADER), end=bcolors.ENDC + '\n')

    # HEADER
    print('{:<1s}'.format('|'), end=' ')
    print('{:<25}'.format(bcolors.BOLD + bcolors.HEADER + 'Masternode' + bcolors.ENDC), end=' ')
    print('{:<25}'.format(bcolors.BOLD + 'IP-Address' + bcolors.ENDC), end=' ')
    print('{:>4s}'.format('MAX'), end=' ')
    print('{:1s}'.format('|'), end=' ')
    print('{:>4s}'.format('PO'), end=' ')
    print('{:>3s}'.format(''), end='')
    print('{:<1s}'.format('%'), end=' ')
    print('{:>3s}'.format('|'), end=' ')
    print('{:>6s}'.format('rMAX'), end=' ')
    print('{:1s}'.format('|'), end=' ')
    print('{:>4s}'.format('rPO'), end=' ')
    print('{:>3s}'.format(''), end='')
    print('{:>1s}'.format('%'), end=' ')
    print('{:>1s}'.format('|'), end=' ')
    print('{:>15s}'.format(bcolors.OKGREEN + 'Proto' + bcolors.ENDC), end=' ')
    print('{:>1s}'.format('|'), end=' ')
    print('{:<18s}'.format(bcolors.OKGREEN + 'sentinel' + bcolors.ENDC), end=' ')
    print('{:1s}'.format('|'), end=' ')
    print('{:<18s}'.format(bcolors.OKGREEN + 'daemon' + bcolors.ENDC), end=' ')
    print('{:1s}'.format('|'), end=' ')
    print('{:<25s}'.format(bcolors.OKBLUE + 'lastpaidtime' + bcolors.ENDC), end=' ')
    print('{:1s}'.format('|'), end=' ')
    print('{:<29s}'.format(bcolors.OKBLUE + 'status' + bcolors.ENDC), end='| \n')

    # END
    print('{:-<153}'.format(bcolors.HEADER), end=bcolors.ENDC + '\n')

    # change dict key str->int
    output = {int(k): dict(v) for k, v in output.items()}

    for line in sorted(output, reverse=True):
        position = output[line]['rank'] / output[line]['max_rank'] * 100
        mn_position = output[line]['mn_rank'] / output[line]['mn_max_rank'] * 100
        pcol = output[line]['protocol'] > 20208 and bcolors.OKGREEN or bcolors.FAIL
        scol = output[line]['sentinelversion'] == '1.2.0' and bcolors.OKGREEN or bcolors.FAIL
        stcol = output[line]['status'] == 'ENABLED' and bcolors.OKGREEN or bcolors.FAIL
        dcol = output[line]['daemonversion'] == '0.12.3.4' and bcolors.OKGREEN or bcolors.FAIL
        paycol = bcolors.OKBLUE

        last_paid_time_h = timeCalc(now - output[line]['lastpaidtime'])

        last_paid_time_x = datetime.datetime.utcfromtimestamp(output[line]['lastpaidtime']).strftime('%Y-%m-%d %H:%M')

        print('{:<1s}'.format('|'), end=' ')
        print('{:<25}'.format(bcolors.BOLD + bcolors.OKBLUE + output[line]['alias'] + bcolors.ENDC), end=' ')
        print('{:<25}'.format(bcolors.BOLD + output[line]['address'].split(':')[0] + bcolors.ENDC), end=' ')
        print('{:4d}'.format(output[line]['max_rank']), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:>4d}'.format(output[line]['rank']), end=' ')
        print('{:>3d}'.format(round(position)), end='')
        print('{:<1s}'.format('%'), end=' ')
        print('{:>3s}'.format('|'), end=' ')
        print('{:6d}'.format(output[line]['mn_max_rank']), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:>4d}'.format(output[line]['mn_rank']), end=' ')
        print('{:>3d}'.format(round(mn_position)), end='')
        print('{:1s}'.format('%'), end=' ')
        print('{:>1s}'.format('|'), end=' ')
        print('{:>15s}'.format(pcol + str(output[line]['protocol']) + bcolors.ENDC), end=' ')
        print('{:>1s}'.format('|'), end=' ')
        print('{:<18s}'.format(scol + str(output[line]['sentinelversion']) + bcolors.ENDC), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:<18s}'.format(dcol + str(output[line]['daemonversion']) + bcolors.ENDC), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:<25s}'.format(paycol + last_paid_time_h + bcolors.ENDC), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:<25s}'.format(stcol + str(output[line]['status'])), end=bcolors.ENDC + '| \n')

    print('{:-<153}'.format(bcolors.HEADER), end=bcolors.ENDC + '\n')
    print('amountof listed MASTERNODES [' + str(len(output)) + ']')


def mainControl():
    checkMnSync()

    #### Write the FILES ####
    writeCache(cliCmd('masternode list', False), './mn_list.json')
    writeCache(cliCmd('masternode list rank', False), './mn_rank.json')
    writeMnCache(cliCmd('masternode list-conf', False), "./mn_conf.json")

    #### Open the FILES ####
    list_file = open('mn_list.json', 'r')
    list_dic = json.load(list_file, object_pairs_hook=OrderedDict)
    list_file.close()
    rank_file = open('mn_rank.json', 'r')
    rank_dic = json.load(rank_file, object_pairs_hook=OrderedDict)
    rank_file.close()
    conf_file = open('mn_conf.json', 'r')
    conf_dic = json.load(conf_file, object_pairs_hook=OrderedDict)
    rank_file.close()

    ### Fill global VARS ###

    global enabled_mn
    enabled_mn = readEnabled(list_dic)


    #### Write output FILES ####
    writeMnOutput(conf_dic, list_dic, rank_dic, './mn_output.json')
    output_file = open('./mn_output.json', 'r')
    output_dic = json.load(output_file, object_pairs_hook=OrderedDict)
    output_file.close()

    ### Print the OutputFile ####
    printOutput(output_dic)


mainControl()
