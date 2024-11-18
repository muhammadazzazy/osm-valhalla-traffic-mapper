# Valhalla Traffic Integration for Careem

## Overview
A Python-based solution for integrating historical traffic data with Valhalla's routing engine to improve ETA accuracy for Careem's ride-hailing platform in Amman, Jordan. This implementation enhances Valhalla's routing capabilities without modifying its core C++ codebase.

## Prerequisites
- Python 3.x
- Osmium Tool
- Valhalla routing engine
- OSRM (for validation)

## Setup and Configuration
### Installing Valhalla
Follow the [gis-ops guide for installing Valhalla on Ubuntu](https://gis-ops.com/valhalla-part-1-how-to-install-on-ubuntu/#Introduction).

### Running Valhalla
For basic Valhalla configuration and running instructions, see the [gis-ops guide for running Valhalla](https://gis-ops.com/valhalla-part-2-how-to-run-valhalla-on-ubuntu/).

### Project-Specific Setup
After installing and configuring Valhalla:
1. Clone the repository:
   ```bash
   git clone https://github.com/muhammadazzazy/osm-valhalla-traffic-mapper.git
   cd osm-valhalla-traffic-mapper
   ```
2. Download Jordan OSM data:
   ```bash
   ./scripts/download_jordan_osm.sh
   ```
3. Extract Amman region:
   ```bash
   ./scripts/extract_amman_data.sh
   ```
4. Process speed data:
   ```bash
   python src/predicted_speeds.py
   ```

## Project Structure
```
osm-valhalla-traffic-mapper/
├── src/
│   ├── routes.py                 # OSRM vs Valhalla distance comparison logic
│   ├── graph_id.py               # Graph ID processing
│   ├── predicted_speeds.py       # Historical speeds conversion to DCT-II functionality
│   ├── main.py                   # Traffic CSV file preparation and writing utilities 
│   ├── get_etas.py               # Valhalla ETA extraction functionality
│   ├── speeds_checker.py         # Speed-limit violation validator
│   ├── speeds_extractor.py       # Speed data extraction from JSON
│   └── valhalla_way_id_mapper.py # OSM way ID mapping tools
├── scripts/
│   ├── download_jordan_osm.sh    # Script to download Jordan OSM data
│   └── extract_amman_data.sh     # Script to extract Amman region data using Osmium
```

### Source Files (`src/`)
#### Route Processing
- `routes.py`: Validates routing accuracy by comparing Valhalla and OSRM distance calculations
- `get_etas.py`: Extracts and processes ETAs from Valhalla
- `graph_id.py`: Handles Valhalla graph ID conversion and processing

#### Speed Data Management
- `predicted_speeds.py`: Converts historical speed data using DCT-II functionality
- `speeds_checker.py`: Validates speed data against Jordan's traffic regulations
- `speeds_extractor.py`: Extracts speed data from JSON format

#### Data Integration
- `main.py`: Prepares and writes traffic CSV files
- `valhalla_way_id_mapper.py`: Maps OSM way IDs to coordinates

### Scripts (`scripts/`)
- `download_jordan_osm.sh`: Downloads latest Jordan OSM data
- `extract_amman_data.sh`: Extracts Amman-specific region using Osmium

## Core Components
### Routing System Integration
The system integrates with Valhalla through:
- Graph ID conversion matching Valhalla's internal format
- OSM way ID mapping for coordinate pairs
- Batch processing support for routing requests

### Traffic Data Processing
Processes historical traffic data to enhance ETA accuracy:
- Analyzes 2016 weekly speed patterns (5-minute intervals)
- Extracts day/night speed variations
- Validates against local speed limits
- Prepares data in Valhalla-compatible format

## Contributing
Contributions welcome via pull requests.

## Acknowledgments
- OpenStreetMap contributors
- Valhalla and OSRM teams
