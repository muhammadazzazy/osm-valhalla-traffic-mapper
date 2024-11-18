import csv
import requests
import numpy as np
from math import sqrt

# 'JO': ('Jordan', (34.9226025734, 29.1974946152, 39.1954683774, 33.3786864284))
MIN_LAT = 29.1974946152
MIN_LNG = 34.9226025734
MAX_LAT = 33.3786864284
MAX_LNG = 39.1954683774

# Function to read latitude and longitude coordinates from a CSV file
# It returns a list of tuples where each tuple contains a source and destination pair
def read_coords(file_path):
    coords = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        rows = list(csv_reader)

        # Loop through the rows and group them into source and destination pairs
        for i in range(0, len(rows) - 1, 2):
            src = (float(rows[i]['pickup_latitude']), float(rows[i]['pickup_longitude']))
            dest = (float(rows[i + 1]['pickup_latitude']), float(rows[i + 1]['pickup_longitude']))
            if MIN_LAT <= src[0] <= MAX_LAT and MIN_LNG <= src[1] <= MAX_LNG:
                if MIN_LAT <= dest[0] <= MAX_LAT and MIN_LNG <= dest[1] <= MAX_LNG:
                    if src != dest:
                        coords.append((src, dest))
            if len(coords) == 500:
                break

    print(len(coords))

    return coords

# Function to get OSRM route from local Docker container
def get_osrm_route(src, dest):
    osrm_url = "http://localhost:5000/route/v1/driving/"
    coords_str = f"{src[1]},{src[0]};{dest[1]},{dest[0]}"
    response = requests.get(f"{osrm_url}{coords_str}?overview=false")
    if response.status_code == 200:
        osrm_response = response.json()
        return osrm_response
    else:
        raise Exception(f"OSRM request failed with status code {response.status_code}")

# Function to get Valhalla route from local Docker container
def get_valhalla_route(source, destination):
    valhalla_url = "http://localhost:8002/route"
    locations = [{"lat": source[0], "lon": source[1]}, {"lat": destination[0], "lon": destination[1]}]
    request_body = {
        "locations": locations,
        "costing": "auto",
        "directions_options": {"units": "kilometers"}
    }
    response = requests.post(valhalla_url, json=request_body)
    if response.status_code == 200:
        valhalla_response = response.json()
        return valhalla_response
    else:
        raise Exception(f"Valhalla request failed with status code {response.status_code}")

# Function to calculate statistics between OSRM and Valhalla distances
def compute_metrics(lengths, distances):
    assert len(lengths) == len(distances), "Valhalla and OSRM distances must have the same length."

    lengths = np.array(lengths)
    distances = np.array(distances)

    avg_dists = (lengths + distances) / 2

    diffs = lengths - distances
    abs_diffs = np.abs(diffs)
    percent_diffs = 100 * abs_diffs / avg_dists

    metrics = {
        "Average Percentage Difference": np.mean(percent_diffs),
        "Minimum Percentage Difference": np.min(percent_diffs),
        "Maximum Percentage Difference": np.max(percent_diffs),
        "Average Absolute Difference": np.mean(abs_diffs),
        "Minimum Absolute Difference": np.min(abs_diffs),
        "Maximum Absolute Difference": np.max(abs_diffs),
        "RMSE": sqrt(np.mean(np.square(diffs)))
    }
    return metrics

def write_summary(metrics):
    filepath = 'osrm_valhalla_metrics.txt'
    with open(filepath, 'w') as file:
        file.write("Evaluation metrics between Valhalla and OSRM distances:\n")
        file.write(f"Average Percentage Difference: {metrics["Average Percentage Difference"]:.2f}%\n")
        file.write(f"Min Percentage Difference: {metrics["Minimum Percentage Difference"]:.2f}%\n")
        file.write(f"Max Percentage Difference: {metrics["Maximum Percentage Difference"]:.2f}%\n")
        file.write(f"Average Absolute Difference: {metrics["Average Absolute Difference"]:.2f} km\n")
        file.write(f"Min Absolute Difference: {metrics["Minimum Absolute Difference"]:.2f} km\n")
        file.write(f"Max Absolute Difference: {metrics["Maximum Absolute Difference"]:.2f} km\n")
        file.write(f"RMSE: {metrics["RMSE"]:.2f} km\n")

# Main function to process routes and statistics
def main():
    csv_file_path = 'anon_pooling_jan_24_amman.csv'
    coordinates_pairs = read_coords(csv_file_path)

    distances = []
    lengths = []

    for src, dest in coordinates_pairs:
        try:
            osrm_response = get_osrm_route(src, dest)
            valhalla_response = get_valhalla_route(src, dest)

            distance = osrm_response['routes'][0]['legs'][0]['distance']/1000
            length = valhalla_response['trip']['legs'][0]['summary']['length']

            distances.append(distance)
            lengths.append(length)

            print(f"OSRM Distance from {src} to {dest}: {distance:.2f} km")
            print(f"Valhalla Distance from {src} to {dest}: {length:.2f} km")

        except Exception as e:
            print(f"Error processing route from {src} to {dest}: {e}")

    if distances and lengths:
        metrics = compute_metrics(lengths, distances)
        print("Evaluation metrics between Valhalla and OSRM distances:")
        print(f"Average Percentage Difference: {metrics["Average Percentage Difference"]:.2f}%")
        print(f"Min Percentage Difference: {metrics["Minimum Percentage Difference"]:.2f}%")
        print(f"Max Percentage Difference: {metrics["Maximum Percentage Difference"]:.2f}%")
        print(f"Average Absolute Difference: {metrics["Average Absolute Difference"]:.2f} km")
        print(f"Min Absolute Difference: {metrics["Minimum Absolute Difference"]:.2f} km")
        print(f"Max Absolute Difference: {metrics["Maximum Absolute Difference"]:.2f} km")
        print(f"RMSE: {metrics["RMSE"]:.2f} km")
        write_summary(metrics)

if __name__ == "__main__":
    main()
