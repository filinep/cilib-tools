#!/bin/sh

nice -10 java -Xms1000M -Xmx2500M -cp ../lib/cilib-tools-helper.jar:../lib/cilib-0.7.5.jar:$CLASSPATH simulator.Main $@ 4

