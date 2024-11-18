#!/bin/bash

cd ~/Desktop/valhalla/build

# Extract Amman area using osmium
osmium extract -b 35.715,31.668,36.25,32.171 jordan-latest.osm.pbf -o amman-latest.osm.pbf --overwrite

if [ $? -eq 0 ]; then
    echo "Successfully extracted Amman data to amman-latest.osm.pbf"
else
    echo "Error during extraction"
    exit 1
fi