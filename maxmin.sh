#!/bin/bash
# Find the max and the min for each device in a day's log.
file=$(date +"/home/pi/templog/%Y/%m/%d")
maxmin=/home/pi/templog/maxmin
awk '{for (f=3; f <=NF; ++f) {n=split($f, A, ":"); if (n!=2) print $f; dev=A[1]; temp=A[2]; if (temp==0) print $f; sumt[dev] += temp; countt[dev] += 1; if (maxt[dev]=="" || maxt[dev] < temp) maxt[dev]=temp; if (dev in mint == 0 || mint[dev] > temp) {mint[dev]=temp;}} } END { f=FILENAME; gsub(".*log/", "", f); printf(f); for ( a in maxt) { printf(" %s:%.2f:%.2f:%.2f", a, mint[a], sumt[dev]/countt[dev], maxt[a]);} printf("\n");} ' $file >> ${maxmin}

