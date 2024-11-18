import json
import requests
import os
from typing import Dict, Tuple, Optional
import csv

def get_project_root() -> str:
    """
    Get the project root directory.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_dir, 'data')):
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            raise RuntimeError("Could not find project root with 'data' directory")
        current_dir = parent
    return current_dir

def read_speeds_from_csv(csv_path: str) -> Dict[str, Dict[str, float]]:
    """
    Read the speed data from the CSV file.
    
    Args:
        csv_path: Path to the CSV file containing the speeds
    
    Returns:
        Dict mapping edge_id to dict containing 'free_flow' and 'constrained' speeds
    """
    speeds = {}
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            edge_id = row[0]
            speeds[edge_id] = {
                'free_flow': float(row[1]),
                'constrained': float(row[2])
            }
    return speeds

def extract_coordinates(trip_data: str) -> Tuple[str, int, Tuple[float, float], Tuple[float, float]]:
    """
    Extract the trip ID, segment ID and first/last coordinates from a trip data string.
    
    Args:
        trip_data: Single line of JSON trip data
    
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

def get_valhalla_eta(start_coords: Tuple[float, float], end_coords: Tuple[float, float], 
                     valhalla_url: str, use_traffic: bool = False) -> Optional[float]:
    """
    Get ETA from Valhalla for given coordinates.
    
    Args:
        start_coords: (lat, lng) for start point
        end_coords: (lat, lng) for end point
        valhalla_url: Valhalla server URL
        use_traffic: Whether to use traffic data
    
    Returns:
        float: Estimated time in seconds
    """
    request_json = {
        "locations": [
            {"lat": start_coords[0], "lon": start_coords[1]},
            {"lat": end_coords[0], "lon": end_coords[1]}
        ],
        "costing": "auto",
        "costing_options": {
            "auto": {
                "use_traffic": 1 if use_traffic else 0
            }
        },
        "directions_options": {"units": "kilometers"}
    }
    
    try:
        response = requests.post(f"{valhalla_url}/route", json=request_json)
        response.raise_for_status()
        route_data = response.json()
        return route_data['trip']['summary']['time']
    except requests.exceptions.RequestException as e:
        print(f"Error getting ETA from Valhalla: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text}")
        return None

def process_trips(input_file: str, valhalla_url: str) -> Dict[str, Dict[int, Dict[str, float]]]:
    """
    Process all trips in the input file and get ETAs from Valhalla both with and without traffic.
    
    Args:
        input_file: Path to input JSON file
        valhalla_url: Valhalla server URL
    
    Returns:
        Dict mapping trip_id to segment_id to dict containing 'with_traffic' and 'without_traffic' ETAs
    """
    trip_etas = {}
    
    with open(input_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
                
            # Get trip details
            trip_id, segment_id, start_coords, end_coords = extract_coordinates(line)
            
            # Skip if we've already processed this trip_id and segment_id
            if trip_id in trip_etas and segment_id in trip_etas[trip_id]:
                continue
            
            # Initialize trip_id dict if not exists
            if trip_id not in trip_etas:
                trip_etas[trip_id] = {}
                
            # Get ETAs with and without traffic
            eta_with_traffic = get_valhalla_eta(start_coords, end_coords, valhalla_url, use_traffic=True)
            eta_without_traffic = get_valhalla_eta(start_coords, end_coords, valhalla_url, use_traffic=False)
            
            if eta_with_traffic is not None and eta_without_traffic is not None:
                trip_etas[trip_id][segment_id] = {
                    'with_traffic': eta_with_traffic,
                    'without_traffic': eta_without_traffic
                }
    
    return trip_etas

def write_results(trip_etas: Dict[str, Dict[int, Dict[str, float]]], output_file: str):
    """
    Write trip ETAs to a JSON file.
    
    Args:
        trip_etas: Nested dictionary mapping trip_id to segment_id to ETAs
        output_file: Path to output JSON file
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
    input_file = os.path.join(project_root, 'data', 'input', 'Segmented_Trips_01_25.json')
    output_file = os.path.join(project_root, 'data', 'output', 'ETAs_01_25.json')
    
    # Process trips and get ETAs
    trip_etas = process_trips(input_file, VALHALLA_URL)
    
    # Write results
    write_results(trip_etas, output_file)
    
    # Calculate total number of segments processed
    total_segments = sum(len(segments) for segments in trip_etas.values())
    print(f"Processed {len(trip_etas)} trips with {total_segments} segments and wrote results to {output_file}")
    
    # Print sample of results to verify difference between traffic and non-traffic ETAs
    print("\nSample of results:")
    for trip_id in list(trip_etas.keys())[:3]:
        for segment_id in trip_etas[trip_id]:
            etas = trip_etas[trip_id][segment_id]
            print(f"\nTrip {trip_id}, Segment {segment_id}:")
            print(f"  With traffic: {etas['with_traffic']} seconds")
            print(f"  Without traffic: {etas['without_traffic']} seconds")
            print(f"  Difference: {etas['with_traffic'] - etas['without_traffic']} seconds")

if __name__ == "__main__":
    main()