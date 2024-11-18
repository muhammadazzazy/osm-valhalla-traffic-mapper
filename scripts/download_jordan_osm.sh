# Change to the build directory
cd ~/Desktop/valhalla/build

# Download the Jordan OSM data
wget https://download.geofabrik.de/asia/jordan-latest.osm.pbf

# Check if download was successful
if [ $? -eq 0 ]; then
    echo "Successfully downloaded jordan-latest.osm.pbf to $(pwd)"
else
    echo "Error downloading the file"
    exit 1
fi