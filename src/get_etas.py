import json
import requests
import os
from typing import Dict, Tuple

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
    
    return trip_id, segment_id, (start_lat, start_lng), (end_lat, end_lng)

def get_valhalla_eta(start_coords: Tuple[float, float], end_coords: Tuple[float, float], valhalla_url: str) -> float:
    """
    Get ETA from Valhalla for given coordinates considering traffic.
    """
    request_json = {
        "locations": [
            {"lat": start_coords[0], "lon": start_coords[1]},
            {"lat": end_coords[0], "lon": end_coords[1]}
        ],
        "costing": "auto",
        "directions_options": {"units": "kilometers"},
        "use_traffic": True  # Add traffic-related parameter
    }
    
    try:
        response = requests.post(f"{valhalla_url}/route", json=request_json)
        response.raise_for_status()
        return response.json()['trip']['summary']['time']
    except requests.exceptions.RequestException as e:
        print(f"Error getting ETA from Valhalla: {e}")
        return None


def process_trips(input_file: str, valhalla_url: str) -> Dict[str, Dict[int, float]]:
    """
    Process all trips in the input file and get ETAs from Valhalla.
    
    Args:
        input_file (str): Path to input JSON file
        valhalla_url (str): Valhalla server URL
    
    Returns:
        dict: Nested dictionary mapping trip_id to segment_id to ETA in seconds
    """
    trip_etas = {}
    
    with open(input_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
                
            # Get trip details
            trip_id, segment_id, start_coords, end_coords = extract_trip_info(line)
            
            # Skip if we've already processed this trip_id and segment_id
            if trip_id in trip_etas and segment_id in trip_etas[trip_id]:
                continue
            
            # Initialize trip_id dict if not exists
            if trip_id not in trip_etas:
                trip_etas[trip_id] = {}
                
            # Get ETA from Valhalla
            eta = get_valhalla_eta(start_coords, end_coords, valhalla_url)
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
    # Configuration
    VALHALLA_URL = "http://localhost:8002"  # Adjust this to your Valhalla server URL
    
    # Get project root and construct file paths
    project_root = get_project_root()
    input_file = os.path.join(project_root, 'data', 'input', 'Segmented_Trips_01_27.json')
    output_file = os.path.join(project_root, 'data', 'output', 'ETAs_01_27.json')
    
    # Process trips and get ETAs
    trip_etas = process_trips(input_file, VALHALLA_URL)
    
    # Write results
    write_results(trip_etas, output_file)
    
    # Calculate total number of segments processed
    total_segments = sum(len(segments) for segments in trip_etas.values())
    print(f"Processed {len(trip_etas)} trips with {total_segments} segments and wrote results to {output_file}")

if __name__ == "__main__":
    main()