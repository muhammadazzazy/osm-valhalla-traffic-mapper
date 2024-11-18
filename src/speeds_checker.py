import json
import pandas as pd
import os
from pathlib import Path

def detect_speed_violations(json_file_path):
    """
    Detect speed violations in Amman (speed limit 120 km/h).
    Returns concise violation data including trip ID, speed, and violation details.
    """
    # Process file line by line
    trips = []
    with open(json_file_path, 'r') as file:
        for line in file:
            try:
                trip = json.loads(line.strip())
                # Calculate speed (km/h)                
                time_hours = trip['trip_time'] / 3600
                if time_hours == 0:
                    continue
                speed = trip['dist'] / time_hours
                
                trips.append({
                    'trip_id': trip['trip_id'][:8] + '...',  # Truncate ID for readability
                    'speed': round(speed, 2),
                    'distance': round(trip['dist'], 2),
                    'time_sec': round(trip['trip_time'], 2)
                })
            except json.JSONDecodeError:
                continue
            except KeyError:
                continue

    if not trips:
        print("No valid trips found")
        return None

    # Convert to DataFrame and detect violations
    df = pd.DataFrame(trips)
    violations = df[df['speed'] > 120].copy()
    violations['excess_speed'] = round(violations['speed'] - 120, 2)
    violations = violations.sort_values('excess_speed', ascending=False)

    # Format columns for better readability
    result = pd.DataFrame({
        'Trip ID': violations['trip_id'],
        'Speed (km/h)': violations['speed'],
        'Over Limit By': violations['excess_speed'],
        'Distance (km)': violations['distance'],
        'Time (sec)': violations['time_sec']
    })

    return result

def main():
    # Get project root directory
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Process data for days 25-31
    for day in range(25, 32):
        print(f"\n{'='*50}")
        # Format day with leading zero if needed
        date = f'01_{day:02d}'
        extension = '.json'
        
        try:
            # Build path to input file
            filename = 'Segmented_Trips_'
            file_path = filename + date + extension
            input_path = PROJECT_ROOT / "data" / "input" / file_path
            
            # Process violations
            violations = detect_speed_violations(input_path)
            
            if violations is not None:
                print(f"\nSpeed Violations for {date}:")
                print(violations)
                
                # Save to CSV
                output_file = f"{filename}{date}_violations.csv"
                output_path = PROJECT_ROOT / "data" / "output" / output_file
                violations.to_csv(output_path, index=False)
                print(f"Violations saved to {output_file}")
            else:
                print(f"No violations detected for {date}")
                
        except FileNotFoundError:
            print(f"Warning: Input file not found for {date}")
        except Exception as e:
            print(f"Error processing violations for {date}: {str(e)}")
            
        print(f"{'='*50}\n")

if __name__ == "__main__":
    main()