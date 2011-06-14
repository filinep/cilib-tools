#!/bin/sh

javac -cp ../lib/cilib-0.7.5.jar -d ../build ../java-src/reflection/*.java ../java-src/simulator/*.java
cd ../build
jar cf ../lib/cilib-tools-helper.jar *

