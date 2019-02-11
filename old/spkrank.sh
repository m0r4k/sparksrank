#!/bin/bash

#shows ranks of your masternodes defined in ~/.dashcore/masternodes.conf
#or shows ranks of masternodes specified as arguments. 

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

function cache_output(){
  # cached output
  FILE=$1
  # command to cache
  CMD=$2
  OLD=0
  CONTENTS=""
  # is cache older than 1 minute?
  if [ -e $FILE ]; then
      OLD=$(find $FILE -mmin +1 -ls | wc -l)
      CONTENTS=$(cat $FILE);
  fi
  # is cache empty or older than 1 minute? rebuild
  if [ -z "$CONTENTS" ] || [ "$OLD" -gt 0 ]; then
    CONTENTS=$(eval $CMD)
    echo "$CONTENTS" > $FILE
  fi
  echo "$CONTENTS"
}

getrank()
{
  MNADDR=$1
  MASTERNODE_BIND_IP=$1
  DASH_CLI=sparks-cli
  MN_QUEUE_IN_SELECTION=0
  MN_QUEUE_LENGTH=0
  MN_QUEUE_POSITION=0
  NOW=$(date +%s)
  MN_LIST="$(cache_output /tmp/mnlist_cache '$DASH_CLI masternodelist full 2>/dev/null')"
  SORTED_MN_LIST=$(echo "$MN_LIST" | grep -w ENABLED | sed -e 's/[}|{]//' -e 's/"//g' -e 's/,//g' | grep -v ^$ | \
awk ' \
{
    if ($7 == 0) {
        TIME = $6
        print $_ " " TIME
    }
    else {
        xxx = ("'$NOW'" - $7)
        if ( xxx >= $6) {
            TIME = $6
        }
        else {
            TIME = xxx
        }
        print $_ " " TIME
    }
}' |  sort -k10 -n)
  MN_STATUS=$(   echo "$SORTED_MN_LIST" | grep -m1 $MASTERNODE_BIND_IP | awk '{print $2}')
  MN_PROTO=$(   echo "$SORTED_MN_LIST" | grep -m1 $MASTERNODE_BIND_IP | awk '{print $3}')
  MN_VISIBLE=$(  echo "$MN_STATUS" | wc -l)
  MN_ENABLED=$(  echo "$SORTED_MN_LIST" | grep -c ENABLED)
  MN_UNHEALTHY=$(echo "$SORTED_MN_LIST" | grep -c EXPIRED)
  MN_TOTAL=$(( $MN_ENABLED + $MN_UNHEALTHY ))
  MN_SYNC_ASSET=$(echo "$MN_SYNC_STATUS" | grep 'Asset' | grep -v ID | awk '{print $2}' | sed -e 's/[",]//g' )
  MN_SYNC_COMPLETE=$(echo "$MN_SYNC_STATUS" | grep 'IsSynced' | grep 'true' | wc -l)
  if [ $MN_VISIBLE -gt 0 ]; then
    MN_QUEUE_LENGTH=$MN_ENABLED
    MN_QUEUE_POSITION=$(echo "$SORTED_MN_LIST" | grep ENABLED | grep -A9999999 $MASTERNODE_BIND_IP | wc -l)
    if [ $MN_QUEUE_POSITION -gt 0 ]; then
      MN_QUEUE_IN_SELECTION=$(( $MN_QUEUE_POSITION <= $(( $MN_QUEUE_LENGTH / 10 )) ))
    fi
  fi
  echo $MN_QUEUE_POSITION/$MN_QUEUE_LENGTH"-"$MASTERNODE_BIND_IP"-"$MN_PROTO
}

if [ -z "$1" ]; then
  nodes=$(cat ~/.sparkscore/masternode.conf|grep -v -e ^\#|awk '{print $1}')
else
  nodes=$@
  if [ -z "$nodes" ]; then
    echo "I didn't find any masternodes defined in your masternode.conf.. either add them there .. or specify what masternodes you'd like to see the rank for."
    echo "eg: $0 178.62.229.218:9999 178.62.231.162:9999"
    echo "eg: $0 d81d94bc10c9cad503cca18ea89868b491ef83d1d53144f3c014d2ea2f65ea80-1"
    exit 1
  fi
fi

for m in $nodes
do
  mnaddr=$(cat ~/.sparkscore/masternode.conf |grep -e "^$m "|awk '{print $2} ')
  if [ -z "$mnaddr" ];then
    mnaddr=$m
  fi
  info=$(getrank $mnaddr)
  rank=$(echo $info | cut -d "-" -f 1)
  text=$(echo $info | cut -d "-" -f 2)
  proto=$(echo $info | cut -d "-" -f 3)

  color=$GREEN

  if [[ $proto == *"208"* ]]
  then
    color=$RED
  fi


  echo -e $m ' \t' $rank  $((100*${rank#* }))\% '\t' $text '\t' ${color} $proto ${NC}
done|sort -nk3
