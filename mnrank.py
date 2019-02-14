#!/usr/bin/python3

import json
import subprocess
from collections import OrderedDict
from pathlib import Path
import time
import os
import datetime
import sys
import tempfile



class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Coin:
    # PARAMETERS #
    cache_time_min = 3
    coin_cli = 'sparks-cli'
    tdir = tempfile.gettempdir()

    Config_file = tdir+'/mn.conf'
    list_file = tdir+'/mn_list.json'

    output_file = tdir+'/mn_output.json'
    _now_ = int(datetime.datetime.now().strftime("%s"))


    if len(sys.argv) > 1:
        conf_file = sys.argv[1]
    else:
        conf_file = './mn_conf.json'

    @classmethod
    def checkmnsync(cls):
        check = cls.clicmd('mnsync status')

        if not check['IsSynced']:
            print('you need to wait till mn is synced')
            quit()

        return True

    @classmethod
    def buildfiles(cls):

        cls.checkmnsync()

        if len(sys.argv) == 1:
            if cls.fileage(cls.conf_file) == 0:
                cls.writefile(cls.conf_file, Coin.clicmd(
                    'masternode list-conf', hook='conf-hook'))
        else:
            if cls.fileage(sys.argv[1]) == 0:
                print('config file not found please check')
                cls.stdconf(sys.argv[1])
            else:
                print('file found ' + sys.argv[1])

        if cls.fileage(cls.list_file) == 0 or cls.fileage(cls.list_file) >= cls.cache_time_min:
            cls.writefile(cls.list_file, Coin.clicmd('masternode list'))

    @classmethod
    def stdconf(cls, filename=''):

        if filename == '':
            filename = cls.list_file

        _stdconf_dict = {
            'seed1_mn': '80.211.65.29',
            'seed2_mn': '80.211.57.4',
            'seed3_mn': '51.15.112.11',
            'seed4_mn': '94.177.176.181',
        }

        cls.writefile(filename, _stdconf_dict)

    @classmethod
    def clicmd(cls, cmd, hook=''):
        try:
            cli_output = subprocess.check_output(
                cls.coin_cli + ' ' + cmd, shell=True).decode("utf-8")

            if hook == 'conf-hook':
                iter_num = 0
                output = ""
                iter_string = ""
                mnconf_json = {}
                # masternode list-conf INDEX HOOK makes name-ip json
                for i in cli_output.split('\"masternode\"'):
                    if iter_num != 0:
                        iter_string = '\"' + str(iter_num) + '\"'

                    output = "".join([output, iter_string + ' ' + i])
                    iter_num = iter_num + 1

                output_json = json.loads(output, object_pairs_hook=OrderedDict)

                for i in output_json:
                    mnconf_json[output_json[i]['alias']] = output_json[i]['address'].split(':')[
                        0]
                return mnconf_json

            cli_output = json.loads(cli_output, object_pairs_hook=OrderedDict)
            return cli_output
        except subprocess.CalledProcessError:
            quit()

    @staticmethod
    def fileage(filename):
        exists = Path(filename)
        if exists.is_file():
            age = time.time() - os.path.getmtime(filename)
        else:
            age = 0
        # returns age in minutes
        return age / 60

    @classmethod
    def writefile(cls, filename, data, sort_keys=True, indent=4):


        file_age = cls.fileage(filename)
        if file_age > cls.cache_time_min or file_age == 0:
            Path(filename).write_text(json.dumps(
                data, sort_keys=sort_keys, indent=indent))
        return ()

    @classmethod
    def rankcalc(cls, lastpaidtime, activeseconds):
        if int(lastpaidtime) == 0:
            rank = activeseconds
        else:
            delta = cls._now_ - lastpaidtime
            if delta >= int(activeseconds):
                rank = activeseconds
            else:
                rank = delta
        return rank

    @classmethod
    def filteranks(cls, dictdata, mndata):
        r_data = {}
        pos_data = {}
        mn_conf_ips = []
        for i in mndata:
            mn_conf_ips.append(mndata[i].split(':')[0])

        for i in dictdata:
            status = dictdata[i]['status']
            ip = dictdata[i]['address'].split(':')[0]

            if ip in mn_conf_ips:
                r_data[i] = dictdata[i]
                pos_data[i] = cls.rankcalc(
                    dictdata[i]['lastpaidtime'], dictdata[i]['activeseconds'])
            elif status == 'ENABLED' or status == 'SENTINEL_PING_EXPIRED':
                r_data[i] = dictdata[i]
                pos_data[i] = cls.rankcalc(
                    dictdata[i]['lastpaidtime'], dictdata[i]['activeseconds'])

        # sort pos_data to get position
        sorted_pos_data = sorted(
            pos_data.items(), key=lambda kv: kv[1], reverse=True)

        sorted_list = []
        for i in sorted_pos_data:
            sorted_list.append(i[0])

        for i in sorted_list:
            r_data[i] = dictdata[i]
            r_data[i]['pos'] = sorted_list.index(i)

        return r_data

    @staticmethod
    def openfile(filename):
        exists = Path(filename)
        if exists.is_file():
            _file = open(filename, 'r')
            _file_dic = json.load(_file, object_pairs_hook=OrderedDict)
            _file.close()
            return _file_dic

        return dict()

    @classmethod
    def ip2txid(cls, list_dict, conf_dict):
        ip_name = {}
        ip_pos = {}
        ip_txid = {}
        r_data = {}

        for i in conf_dict:
            ip_name[conf_dict[i]] = i

        for i in list_dict:
            ip_txid[list_dict[i]['address'].split(':')[0]] = i
            ip_pos[list_dict[i]['address'].split(':')[0]] = list_dict[i]['pos']

        for i in ip_name:
            r_data[ip_pos[i]] = [ip_txid[i], ip_name[i]]

        return r_data

    @staticmethod
    def timeCalc(time):
        if time > 0:
            day = time // (24 * 3600)
            time = time % (24 * 3600)
            hour = time // 3600
            time %= 3600
            minutes = time // 60
            time %= 60
            return str(str(day).zfill(2) + 'd ' + str(hour).zfill(2) + ':' + str(minutes).zfill(2))
        else:
            return str('00d 00:00')

    @classmethod
    def printoutput(cls):
        list_dict = cls.openfile(cls.list_file)
        conf_dict = cls.openfile(cls.conf_file)
        list_dict_filtered = cls.filteranks(list_dict, conf_dict)

        list_dict_txid = cls.ip2txid(list_dict_filtered, conf_dict)
        list_dict_txid_reversed = OrderedDict(
            reversed(list(list_dict_txid.items())))

        # rename for easy lines
        _output = list_dict_txid_reversed
        _list = list_dict_filtered
        _max_rank = len(_list)
        now = int(datetime.datetime.now().strftime("%s"))

        # BEGIN
        print('{:-<132}'.format(bcolors.HEADER + '' + bcolors.ENDC), end=' \n')

        # HEADER
        print('{:<1s}'.format(bcolors.ENDC + '|'), end=' ')
        print('{:<25}'.format(bcolors.BOLD + bcolors.HEADER + 'Masternode' + bcolors.ENDC), end=' ')
        print('{:<25}'.format(bcolors.BOLD + 'IP-Address' + bcolors.ENDC), end=' ')
        print('{:>4s}'.format('MAX'), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:>4s}'.format('PO'), end=' ')
        print('{:>3s}'.format(''), end='')
        print('{:<1s}'.format('%'), end=' ')
        print('{:>3s}'.format('|'), end=' ')
        print('{:>15s}'.format(bcolors.OKGREEN + 'Proto' + bcolors.ENDC), end=' ')
        print('{:>1s}'.format('|'), end=' ')
        print('{:<18s}'.format(bcolors.OKGREEN + 'sentinel' + bcolors.ENDC), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:<18s}'.format(bcolors.OKGREEN + 'daemon' + bcolors.ENDC), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:<18s}'.format(bcolors.OKBLUE + 'lastpaid' + bcolors.ENDC), end=' ')
        print('{:1s}'.format('|'), end=' ')
        print('{:<31s}'.format(bcolors.OKBLUE + 'status' + bcolors.ENDC), end=' |\n')

        # END
        print('{:-<132}'.format(bcolors.HEADER + bcolors.ENDC), end='\n')

        for line in sorted(_output, reverse=False):
            txid = _output[line][0]
            _name = _output[line][1]
            _out = _list[txid]

            position = _out['pos'] / _max_rank * 100
            pcol = _out['protocol'] > 20208 and bcolors.OKGREEN or bcolors.FAIL
            scol = _out['sentinelversion'] == '1.2.0' and bcolors.OKGREEN or bcolors.FAIL
            stcol = _out['status'] == 'ENABLED' and bcolors.OKGREEN or bcolors.FAIL
            dcol = _out['daemonversion'] == '0.12.3.4' and bcolors.OKGREEN or bcolors.FAIL
            paycol = bcolors.OKBLUE

            last_paid_time_h = cls.timeCalc(now - _out['lastpaidtime'])

            print('{:<1s}'.format(bcolors.ENDC + '|'), end=' ')
            print('{:<25}'.format(bcolors.BOLD + bcolors.OKBLUE + _name + bcolors.ENDC), end=' ')
            print('{:<25}'.format(bcolors.BOLD + _out['address'].split(':')[0] + bcolors.ENDC), end=' ')
            print('{:4d}'.format(_max_rank), end=' ')
            print('{:1s}'.format('|'), end=' ')
            print('{:>4d}'.format(_out['pos']), end=' ')
            print('{:>3d}'.format(round(position)), end='')
            print('{:<1s}'.format('%'), end=' ')
            print('{:>3s}'.format('|'), end=' ')
            print('{:>15s}'.format(pcol + str(_out['protocol']) + bcolors.ENDC), end=' ')
            print('{:>1s}'.format('|'), end=' ')
            print('{:<18s}'.format(scol + str(_out['sentinelversion']) + bcolors.ENDC), end=' ')
            print('{:1s}'.format('|'), end=' ')
            print('{:<18s}'.format(dcol + str(_out['daemonversion']) + bcolors.ENDC), end=' ')
            print('{:1s}'.format('|'), end=' ')
            print('{:<18s}'.format(paycol + last_paid_time_h + bcolors.ENDC), end=' ')
            print('{:1s}'.format('|'), end=' ')
            print('{:<28s}'.format(stcol + str(_out['status'])), end=bcolors.ENDC + '| \n')

        print('{:-<132}'.format(bcolors.HEADER + bcolors.ENDC), end='\n')
        print('amountof listed MASTERNODES [' + str(len(conf_dict)) + ']')


Coin.buildfiles()
Coin.printoutput()
