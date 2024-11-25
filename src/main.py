# import the necessary packages
import csv
import os
from pathlib import Path
import json

from graph_id import GraphId

def read_way_edges(filepath):
    """
    Reads the way_edges.txt file and extracts the graph IDs in a dictionary

    :param filepath: The filepath to the way_edges.txt file.
    :return: A dictionary indexed by the OSM way ID and containing a tuple of the direction and the graph ID.
    """
    way_edges = {}

    with open(filepath, 'r') as file:
        for line in file:
            parts = line.strip().split(',')

            osm_way_id = parts[0]
            # print(osm_way_id)

            dirs_gph_ids = parts[1:]
            # print(dirs_gph_ids)

            # Initialize list for the current osm_way_id if not already present
            if osm_way_id not in way_edges:
                way_edges[osm_way_id] = []

            # Iterate over the graph ids, converting them to GraphId objects
            for i in range(0, len(dirs_gph_ids), 2):
                direction = dirs_gph_ids[i]
                gph_id = int(dirs_gph_ids[i + 1])

                # Create a GraphId object from the graph_id (64-bit value)
                graph_id = GraphId(value=gph_id)

                # Store (direction, GraphId) tuple in the dictionary
                way_edges[osm_way_id].append((direction, graph_id))

    return way_edges

def extract_file_names(directory, extension):
    """
    Extracts file names with a specific extension from a directory recursively.

    :param directory: The root directory to start searching.
    :param extension: The file extension to filter (e.g., '.txt', '.jpg').
    :return: A list of file paths with the specified extension.
    """
    file_names = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                file_names.append(os.path.join(root, file))
    return file_names

def write_csv_from_gph(gph_paths, way_edges, daytime_speeds_file, nighttime_speeds_file):
    """
    Writes CSV files with the same names as the .gph files based on the way_edges dictionary.
    Creates all necessary directories in the valhalla_traffic structure.
    Uses speed data from JSON files for freeflow (nighttime) and constrained (daytime) speeds.
    
    :param gph_paths: List of file paths for the .gph files.
    :param way_edges: Dictionary with OSM Way ID as keys and (direction, graph_id) tuples as values.
    :param daytime_speeds_file: Path to JSON file containing daytime speeds
    :param nighttime_speeds_file: Path to JSON file containing nighttime speeds
    """
    # Default speeds (km/h)
    DEFAULT_FREEFLOW_SPEED = 50
    DEFAULT_CONSTRAINED_SPEED = 40
    
    # Load speed data from JSON files
    try:
        with open(daytime_speeds_file, 'r') as f:
            daytime_speeds = json.load(f)
        with open(nighttime_speeds_file, 'r') as f:
            nighttime_speeds = json.load(f)
    except Exception as e:
        print(f"Error loading speed files: {e}")
        return
    
    count = 0
    # Create main valhalla_traffic directory if needed
    for gph_path in gph_paths:
        # Get directory and modify it for traffic data
        original_dir = os.path.dirname(gph_path)
        traffic_dir = original_dir.replace('valhalla_tiles', 'valhalla_traffic')
        
        # Create the full directory path
        try:
            os.makedirs(traffic_dir, exist_ok=True)
            print(f"Created directory: {traffic_dir}")
        except Exception as e:
            print(f"Error creating directory {traffic_dir}: {e}")
            continue
            
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(gph_path))[0]
        
        # Set CSV output path
        csv_path = os.path.join(traffic_dir, f"{base_name}.csv")
        
        # Prepare to write to CSV
        with open(csv_path, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            
            # Write edge data only if the condition is met
            for osm_way_id, graph_info in way_edges.items():
                # Get speeds for this way, default to default speeds if not found
                freeflow_speed = round(float(nighttime_speeds.get(osm_way_id, DEFAULT_FREEFLOW_SPEED)))
                constrained_speed = round(float(daytime_speeds.get(osm_way_id, DEFAULT_CONSTRAINED_SPEED)))
                
                # Extract the last 3 digits before the second slash
                for direction, graph_id in graph_info:
                    if '/' in str(graph_id):
                        parts = str(graph_id).split('/')
                        if len(parts) == 3 and len(parts[1]) >= 3:  # Check if there's a second part and it's long enough
                            last_three_digits = parts[1][-3:]  # Get last 3 digits before the second slash
                            if last_three_digits == base_name:  # Compare with base_name
                                edge_id = str(graph_id)  # Use graph_id as edge_id
                                csv_writer.writerow([edge_id, freeflow_speed, constrained_speed])
                                count += 1
                                print(f"Wrote to CSV: {edge_id}")
            
        print(count)
        print(f"CSV file written to: {csv_path}")


def delete_files(directory, extension):
    """
    Recursively deletes all files with a specific extension in the specified directory and its subdirectories.

    :param directory: The root directory to start the search and deletion.
    :param extension: The extension of the files to be deleted.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"Deleted: {file_path}")

def main():
    """Main function."""
    traffic_path = "/home/muhammad-azzazy/Desktop/valhalla/build/custom_files/valhalla_traffic"
    # Delete the existing traffic CSV files from the tiles directory
    delete_files(traffic_path, extension='.csv')

    # Read the way edges from the way_edges.txt which was previously generated by Valhalla
    # Get project root directory
    PROJECT_ROOT = Path(__file__).parent.parent
    txt_extension = '.txt'
    file_name = f'way_edges{txt_extension}'
    file_path = PROJECT_ROOT / "data" / "input" / file_name
    way_edges = read_way_edges(file_path)

    print("Graph IDs read from way_edges.txt")

    for osm_way_id, graph_info in way_edges.items():
        print(f"OSM Way ID: {osm_way_id}")
        for direction, graph_id in graph_info:
            print(f"\tDirection: {direction}, GraphId: {str(graph_id)}")

    # Extract the file paths of the .gph files from the tiles directory generated by Valhalla
    tiles_path = '/home/muhammad-azzazy/Desktop/valhalla/build/custom_files/valhalla_tiles'
    file_paths = extract_file_names(tiles_path, extension=".gph")
    print("File paths:")
    print(file_paths)
    print(len(file_paths))

    # Extract the file names of the .gph files from the extracted file paths
    file_names = []
    for file_path in file_paths:
        file_names.append(os.path.basename(file_path))
    print(file_names)
    
    file_names = [file_path.split('/')[-1].split('.')[0] for file_path in file_paths]

    # Write the traffic information to the CSV files according to Valhalla's file naming and directory structure
    # conventions
    date = '01_31'
    json_extension = '.json'
    daytime_speeds_filename = f'osm_way_daytime_speeds_{date}{json_extension}'
    daytime_speeds_path = PROJECT_ROOT / "data" / "output" / daytime_speeds_filename
    
    nighttime_speeds_filename = f'osm_way_nighttime_speeds_{date}{json_extension}'
    nighttime_speeds_path = PROJECT_ROOT / "data" / "output" / nighttime_speeds_filename
    write_csv_from_gph(file_paths, way_edges, daytime_speeds_path, nighttime_speeds_path)
    print(f"Traffic CSV files successfully written to {traffic_path}.")

if __name__ == "__main__":
    main()
