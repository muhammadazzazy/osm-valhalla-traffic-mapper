import json
import requests
import os
import argparse
from typing import Dict, Tuple
from datetime import datetime, timedelta

def convert_minutes_to_iso8601(date, minutes_from_midnight):
    """
    Convert minutes from midnight to ISO 8601 datetime format.
    
    Args:
        date (str): Date in 'YYYY-MM-DD' format.
        minutes_from_midnight (int): Time in minutes from 12:00 AM.
    
    Returns:
        str: ISO 8601 formatted datetime string.
    """
    # Parse the date
    base_datetime = datetime.strptime(date, "%Y-%m-%d")
    
    # Add the minutes to midnight
    target_datetime = base_datetime + timedelta(minutes=minutes_from_midnight)
    
    # Format to ISO 8601
    return target_datetime.strftime("%Y-%m-%dT%H:%M")

def get_project_root() -> str:
    """
    Get the project root directory.
    Assumes this script is run from any directory within the project.
    
    Returns:
        str: Absolute path to project root
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_dir, 'data')):
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            raise RuntimeError("Could not find project root with 'data' directory")
        current_dir = parent
    return current_dir

def extract_trip_info(trip_data: str) -> Tuple[str, int, Tuple[float, float], Tuple[float, float]]:
    """
    Extract the trip ID, segment ID, and first/last coordinates from a trip data string.
    
    Args:
        trip_data (str): Single line of JSON trip data
    
    Returns:
        tuple: (trip_id, segment_id, (start_lat, start_lng), (end_lat, end_lng))
    """
    data = json.loads(trip_data)
    trip_id = data['trip_id']
    segment_id = data['segmentID']
    
    # Get first and last coordinates
    start_lat = float(data['lats'][0])
    start_lng = float(data['lngs'][0])
    end_lat = float(data['lats'][-1])
    end_lng = float(data['lngs'][-1])
    time_id = int(data['timeID'])
    
    return trip_id, segment_id, (start_lat, start_lng), (end_lat, end_lng), time_id

def get_valhalla_eta(start_coords: Tuple[float, float], end_coords: Tuple[float, float], valhalla_url: str, date_time) -> float:
    """
    Get ETA from Valhalla for given coordinates considering traffic.
    """
    if start_coords == end_coords:
        print(f"Skipping Valhalla request: Start and end coordinates are identical: {start_coords}")
        return None
    
    request_json = {
        "locations": [
            {"lat": start_coords[0], "lon": start_coords[1]},
            {"lat": end_coords[0], "lon": end_coords[1]}
        ],
        "costing": "auto",
        "directions_options": {"units": "kilometers"},
        "use_traffic": True,  # Add traffic-related parameter
        "date_time": {
            "type": 1,  # Use a specific departure time
            "value": date_time
        }
    }
    
    try:
        response = requests.post(f"{valhalla_url}/route", json=request_json)
        response.raise_for_status()
        return response.json()['trip']['summary']['time']
    except requests.exceptions.RequestException as e:
        print(f"Error getting ETA from Valhalla: {e}")
        return None

def process_trips(input_file: str, valhalla_url: str, date: str) -> Dict[str, Dict[int, float]]:
    """
    Process all trips in the input file and get ETAs from Valhalla.
    
    Args:
        input_file (str): Path to input JSON file
        valhalla_url (str): Valhalla server URL
        date (str): Date in YYYY-MM-DD format
    
    Returns:
        dict: Nested dictionary mapping trip_id to segment_id to ETA in seconds
    """
    trip_etas = {}
    
    with open(input_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
                
            # Get trip details
            trip_id, segment_id, start_coords, end_coords, time_id = extract_trip_info(line)
            print(time_id)

            # Skip if we've already processed this trip_id and segment_id
            if trip_id in trip_etas and segment_id in trip_etas[trip_id]:
                continue
            
            # Initialize trip_id dict if not exists
            if trip_id not in trip_etas:
                trip_etas[trip_id] = {}
                
            # Get ETA from Valhalla
            date_time = convert_minutes_to_iso8601(date, time_id)
            print(trip_id)
            print(date_time)

            eta = get_valhalla_eta(start_coords, end_coords, valhalla_url, date_time)
            if eta is not None:
                trip_etas[trip_id][segment_id] = eta
    
    return trip_etas

def write_results(trip_etas: Dict[str, Dict[int, float]], output_file: str):
    """
    Write trip ETAs to a JSON file.
    
    Args:
        trip_etas (dict): Nested dictionary mapping trip_id to segment_id to ETA
        output_file (str): Path to output JSON file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(trip_etas, f, indent=2)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process trip data with specified date.')
    parser.add_argument('date', type=str, help='Date in MM_DD format (e.g., 01_25)')
    args = parser.parse_args()
    
    # Convert MM_DD format to YYYY-MM-DD format
    date_parts = args.date.split('_')
    full_date = f"2024-{date_parts[0]}-{date_parts[1]}"
    
    # Configuration
    VALHALLA_URL = "http://localhost:8002"  # Adjust this to your Valhalla server URL
    
    # Get project root and construct file paths
    project_root = get_project_root()
    input_file = os.path.join(project_root, 'data', 'input', f'Segmented_Trips_{args.date}.json')
    output_file = os.path.join(project_root, 'data', 'output', f'ETAs_{args.date}.json')
    
    # Process trips and get ETAs
    trip_etas = process_trips(input_file, VALHALLA_URL, full_date)
    
    # Write results
    write_results(trip_etas, output_file)
    
    # Calculate total number of segments processed
    total_segments = sum(len(segments) for segments in trip_etas.values())
    print(f"Processed {len(trip_etas)} trips with {total_segments} segments and wrote results to {output_file}")

if __name__ == "__main__":
    main()