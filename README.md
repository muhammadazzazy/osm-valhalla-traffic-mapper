# Optimizing the Platform of Careem, the Ride Hailing Company

## Overview
This repository contains a collection of Python and Bash scripts developed as part of my senior project focused on optimizing Careem's ride-hailing platform in Amman, Jordan. The project primarily aims to improve ETA accuracy by incorporating historical traffic data into Valhalla's routing engine, without modifying Valhalla's source code.

## Key Features
- Amman-specific OSM Data Processing
- Routing Engine Validation (Valhalla vs OSRM)
- Valhalla Graph ID Conversion
- Day/Night Speed Extraction for Obtaining Freeflow and Constrained Speeds
- Coordinate-to-OSM Way ID Mapping
- Historical Traffic Speeds Processing

## Prerequisites
- Python 3.x
- Osmium Tool
- Valhalla routing engine
- OSRM (for validation)

## Project Structure
```
osm-valhalla-traffic-mapper/
├── src/
│   ├── get_etas.py              # ETA calculation utilities
│   ├── graph_id.py              # Graph ID processing
│   ├── graphid.py               # Valhalla graph ID conversion implementation
│   ├── main.py                  # Main application entry point
│   ├── predicted_speeds.py      # Historical speeds conversion to DCT-II implementation
│   ├── routes.py                # Route processing utilities
│   ├── speeds_checker.py        # Speed-limit violation logic
│   ├── speeds_extractor.py      # Speed data extraction from JSON
│   └── valhalla_way_id_mapper.py # OSM way ID mapping tools
├── scripts/
│   ├── download_jordan_osm.sh   # Script to download Jordan OSM data
│   └── extract_amman_data.sh    # Script to extract Amman region data using Osmium
```

## Component Details

### Graph ID Conversion
- **File**: `graphid.py`
- **Purpose**: Implements the equivalent C++ functionality from Valhalla for converting graph IDs
- **Features**:
  - Converts numerical graph IDs to Valhalla string representation
  - Handles way_edges.txt format
  - Compatible with Valhalla's internal ID system

### Historical Traffic Data Processing
- **File**: `predicted_speeds.py`
- **Purpose**: Extract historical traffic data to improve Valhalla's ETA calculations
- **Features**:
  - Processes 2016 weekly speed data assuming 5-minute sampling intervals
  - Extracts actual traffic speeds for different times of day
  - Prepares speed data in a format compatible with Valhalla
  - Enables more accurate ETA predictions without modifying Valhalla's source code

### Routing Integration
- **File**: `valhalla_way_id_mapper.py`
- **Features**:
  - Integrates with Valhalla routing engine
  - Maps coordinates to OSM way IDs
  - Supports batch processing of coordinate pairs

### Speed Data Incorporation
- **Files**: `speeds_checker.py`, `speeds_extractor.py`
- **Purpose**: Prepare historical traffic data for ETA calculations
- **Features**:
  - Extracts day and night speeds from historical data
  - Processes trip segments with distance and time data
  - Checks for speed-limit violations using Jordan's speed limits for motorways (max speed limit)
  - Prepares speed data for integration with Valhalla

### Route Validation
- **File**: `routes.py`
- **Features**:
  - Compares route distances between Valhalla and OSRM
  - Uses OSRM as ground truth for validation
  - Generates comparison metrics

### OSM Data Processing Scripts
- **Location**: `scripts/`
- **Components**:
  1. `download_jordan_osm.sh`
     - Downloads the latest OpenStreetMap data for Jordan
     - Places the downloaded data in the appropriate directory
     - Streamlines the data acquisition process

  2. `extract_amman_data.sh`
     - Extracts Amman-specific region from Jordan OSM data
     - Filters unnecessary data outside Amman boundaries
     - Places the extracted data in the designated folder
     - Reduces data size by focusing on the Amman region

- **Usage**:
  ```bash
  # Download Jordan OSM data
  ./scripts/download_jordan_osm.sh

  # Extract Amman region
  ./scripts/extract_amman_data.sh
  ```

## Contributing
Contributions are welcome! Please feel free to submit a pull request.

## License
[Specify your license here]

## Acknowledgments
- OpenStreetMap contributors
- Valhalla and OSRM development teams
