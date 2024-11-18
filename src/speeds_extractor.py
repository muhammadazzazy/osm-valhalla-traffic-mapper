import json
from datetime import datetime, time
import copy
import os
from pathlib import Path

def is_daytime(timeID):
    """
    Determine if a given timeID (minutes from midnight) is during daytime (6:00-18:00)
    """
    # Convert timeID (minutes) to hours and minutes
    hours = int(timeID // 60)
    minutes = int(timeID % 60)
    current_time = time(hours, minutes)
    
    # Define daytime as 6:00-18:00
    daytime_start = time(6, 0)
    daytime_end = time(18, 0)
    
    return daytime_start <= current_time < daytime_end

def find_coordinate_changes(lats, lngs):
    """
    Find all source-destination pairs where coordinates change
    """
    pairs = []
    for i in range(len(lats) - 1):
        # If either latitude or longitude changes
        if lats[i] != lats[i + 1] or lngs[i] != lngs[i + 1]:
            src = f"{lats[i]},{lngs[i]}"
            dest = f"{lats[i + 1]},{lngs[i + 1]}"
            pairs.append(f"{src}_{dest}")
    return pairs

def get_speed_limit(area_type='motorway'):
    """
    Return speed limit based on area type
    """
    limits = {
        'motorway': 120,
        'urban': 60,
        'rural': 80
    }
    return limits.get(area_type, 120)  # Default to motorway limit

def calculate_speed(dist, time_seconds):
    """
    Calculate speed in km/h, return None if exceeds motorway limit
    """
    if time_seconds <= 0:
        return None
        
    time_hours = time_seconds / 3600
    speed = dist / time_hours
    
    # Return None if speed exceeds motorway limit
    if speed > get_speed_limit('motorway'):
        return None
    return speed

def process_data(input_data):
    """
    Process the input data and separate into daytime and nighttime speeds
    """
    daytime_speeds = {}
    nighttime_speeds = {}
    
    # Parse each line as a separate JSON object
    trips = [json.loads(line) for line in input_data.strip().split('\n')]
    
    for trip in trips:
        speed = calculate_speed(trip['dist'], trip['trip_time'])
        print(f"\nProcessing trip {trip['trip_id']}")
        
        # Skip this trip's speed if invalid
        if speed is None:
            print(f"Skipping invalid speed for trip {trip['trip_id']}")
            continue
            
        print(f"Trip speed: {speed} km/h")
        
        # Find all coordinate change pairs
        coord_pairs = find_coordinate_changes(trip['lats'], trip['lngs'])
        print(f"Found coordinate pairs: {coord_pairs}")
        
        # Determine if trip is during daytime
        is_day = is_daytime(trip['timeID'])
        print(f"Time: {trip['timeID']} minutes ({'daytime' if is_day else 'nighttime'})")
        
        # Add speed to appropriate dictionary
        speed_dict = daytime_speeds if is_day else nighttime_speeds
        
        for pair in coord_pairs:
            if pair in speed_dict:
                # Update existing pair's speed
                old_avg = speed_dict[pair]['avg_speed']
                speed_dict[pair]['total_speed'] += speed
                speed_dict[pair]['count'] += 1
                speed_dict[pair]['avg_speed'] = (
                    speed_dict[pair]['total_speed'] / speed_dict[pair]['count']
                )
                print(f"Updated existing pair {pair}: {old_avg} -> {speed_dict[pair]['avg_speed']} km/h")
            else:
                # Add new pair
                speed_dict[pair] = {
                    'total_speed': speed,
                    'count': 1,
                    'avg_speed': speed
                }
                print(f"Added new pair {pair} with speed {speed} km/h")
    
    # Convert to final format
    daytime_final = {k: v['avg_speed'] for k, v in daytime_speeds.items()}
    nighttime_final = {k: v['avg_speed'] for k, v in nighttime_speeds.items()}
    
    return daytime_final, nighttime_final

def save_to_json(data, filename):
    """
    Save data to a JSON file
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    # Get project root directory
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Process data for days 25-31
    for day in range(25, 32):
        # Format day with leading zero if needed
        date = f'01_{day:02d}'
        
        # Build path to input file
        filename = 'Segmented_Trips_'
        extension = '.json'
        file_path = filename + date + extension
        input_path = PROJECT_ROOT / "data" / "input" / file_path
        
        try:
            # Read input data
            with open(input_path, 'r') as f:
                input_data = f.read()
                
            # Process the data
            daytime_speeds, nighttime_speeds = process_data(input_data)
            
            # Save results to separate files
            daytime_file_name = 'daytime_speeds_' + date + extension
            nighttime_file_name = 'nighttime_speeds_' + date + extension
            daytime_path = PROJECT_ROOT / "data" / "output" / daytime_file_name
            nighttime_path = PROJECT_ROOT / "data" / "output" / nighttime_file_name
            
            save_to_json(daytime_speeds, daytime_path)
            save_to_json(nighttime_speeds, nighttime_path)
            
            print(f"Successfully processed data for {date}")
            
        except FileNotFoundError:
            print(f"Warning: Input file not found for {date}")
        except Exception as e:
            print(f"Error processing data for {date}: {str(e)}")

if __name__ == "__main__":
    main()