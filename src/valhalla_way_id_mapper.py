import json
import requests
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import time

def get_way_sequence(coord_pair: str, retry_count: int = 3) -> List[Dict]:
    """
    Get full sequence of way IDs with improved matching parameters
    """
    valhalla_url = "http://localhost:8002/trace_attributes"
    
    coords = coord_pair.split('_')
    trace = []
    for coord in coords:
        lat, lon = map(float, coord.split(','))
        trace.append({
            "lat": lat,
            "lon": lon,
            "type": "break"
        })
    
    # Initial payload with more permissive parameters
    payload = {
        "shape": trace,
        "costing": "auto",
        "shape_match": "map_snap",
        "filters": {
            "attributes": ["edge.way_id", "edge.length"],
            "action": "include"
        },
        "directions_options": {
            "units": "kilometers"
        },
        "search_radius": 50,  # 50 meters initial search radius
        "gps_accuracy": 10    # More permissive GPS accuracy
    }
    
    retry_configs = [
        {"search_radius": 50, "gps_accuracy": 10},
        {"search_radius": 100, "gps_accuracy": 20},
        {"search_radius": 200, "gps_accuracy": 30}
    ]
    
    for attempt, config in enumerate(retry_configs):
        try:
            # Update payload with current retry configuration
            payload.update(config)
            
            response = requests.post(valhalla_url, json=payload)
            
            if response.status_code == 400:
                error_msg = response.json().get('error', 'Unknown error')
                if attempt < len(retry_configs) - 1:
                    print(f"Attempt {attempt + 1} failed for {coord_pair}, retrying with larger radius...")
                    time.sleep(0.1)
                    continue
                else:
                    print(f"All attempts failed for {coord_pair}: {error_msg}")
                    return []
                    
            response.raise_for_status()
            
            result = response.json()
            edges = result.get('edges', [])
            
            if not edges:
                if attempt < len(retry_configs) - 1:
                    print(f"No edges found for {coord_pair}, retrying...")
                    continue
                print(f"No edges found for {coord_pair} after all attempts")
                return []
                
            # Process edges
            total_length = sum(edge.get('length', 0) for edge in edges)
            
            way_segments = []
            for edge in edges:
                way_id = edge.get('way_id')
                length = edge.get('length', 0)
                if way_id:
                    weight = length / total_length if total_length > 0 else 0
                    way_segments.append({
                        'way_id': way_id,
                        'length': length,
                        'weight': weight
                    })
            
            if way_segments:
                print(f"Successfully mapped {coord_pair} to {len(way_segments)} way segments")
                return way_segments
            
        except Exception as e:
            if attempt < len(retry_configs) - 1:
                print(f"Error on attempt {attempt + 1} for {coord_pair}: {str(e)}")
                time.sleep(0.1)
                continue
            else:
                print(f"All attempts failed for {coord_pair}: {str(e)}")
                return []
    
    return []

def process_coordinate_pairs(input_data: Dict[str, float]) -> Tuple[Dict[str, float], Dict]:
    """
    Process coordinate pairs with corrected speed calculations
    """
    way_speeds = {}
    stats = {
        'total_pairs': len(input_data),
        'mapped_pairs': 0,
        'failed_pairs': 0,
        'segments_per_pair': {},
        'errors': []
    }
    
    for coord_pair, speed in input_data.items():
        way_segments = get_way_sequence(coord_pair)
        
        if way_segments:
            stats['mapped_pairs'] += 1
            stats['segments_per_pair'][coord_pair] = len(way_segments)
            
            # Each way in the sequence gets the full speed value
            for segment in way_segments:
                way_id = str(segment['way_id'])
                
                if way_id in way_speeds:
                    way_speeds[way_id]['speeds'].append(speed)  # Use original speed
                    total_speeds = way_speeds[way_id]['speeds']
                    # Simple arithmetic mean of all observed speeds
                    way_speeds[way_id]['avg_speed'] = sum(total_speeds) / len(total_speeds)
                else:
                    way_speeds[way_id] = {
                        'speeds': [speed],
                        'avg_speed': speed
                    }
        else:
            stats['failed_pairs'] += 1
            stats['errors'].append(coord_pair)
    
    # Convert to final format
    result = {way_id: data['avg_speed'] for way_id, data in way_speeds.items()}
    
    # Print speed statistics for validation
    speeds = list(result.values())
    if speeds:
        print("\nSpeed Statistics:")
        print(f"Minimum speed: {min(speeds):.2f} km/h")
        print(f"Maximum speed: {max(speeds):.2f} km/h")
        print(f"Average speed: {sum(speeds)/len(speeds):.2f} km/h")
        
        # Print distribution
        ranges = [(0,20), (20,40), (40,60), (60,80)]
        print("\nSpeed Distribution:")
        for low, high in ranges:
            count = sum(1 for s in speeds if low <= s < high)
            print(f"{low}-{high} km/h: {count} ways ({count/len(speeds)*100:.1f}%)")
    
    return result, stats

def main():
    # Get project root directory
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Process data for days 25-31
    for day in range(25, 32):
        # Format day with leading zero if needed
        date = f'01_{day:02d}'
        extension = '.json'
        
        # Process daytime data
        daytime_input_filename = f'daytime_speeds_{date}{extension}'
        daytime_input_path = PROJECT_ROOT / "data" / "output" / daytime_input_filename
        
        try:
            # Read daytime input data
            with open(daytime_input_path, 'r') as f:
                daytime_input_data = json.load(f)
            
            # Process the daytime data
            daytime_result, daytime_stats = process_coordinate_pairs(daytime_input_data)
            
            # Print daytime processing summary
            print(f"\nProcessing Summary for daytime {date}:")
            print(f"Total pairs: {daytime_stats['total_pairs']}")
            print(f"Successfully mapped: {daytime_stats['mapped_pairs']}")
            print(f"Failed to map: {daytime_stats['failed_pairs']}")
            print(f"Success rate: {(daytime_stats['mapped_pairs']/daytime_stats['total_pairs']*100):.2f}%")
            
            print("\nDaytime Segment distribution:")
            daytime_segment_counts = list(daytime_stats['segments_per_pair'].values())
            if daytime_segment_counts:
                print(f"Average segments per pair: {sum(daytime_segment_counts)/len(daytime_segment_counts):.2f}")
                print(f"Max segments for a pair: {max(daytime_segment_counts)}")
                print(f"Min segments for a pair: {min(daytime_segment_counts)}")
            
            # Build daytime output paths
            daytime_speeds_filename = f'osm_way_daytime_speeds_{date}{extension}'
            daytime_stats_filename = f'daytime_mapping_stats_{date}{extension}'
            daytime_speeds_path = PROJECT_ROOT / "data" / "output" / daytime_speeds_filename
            daytime_stats_path = PROJECT_ROOT / "data" / "output" / daytime_stats_filename
            
            # Save daytime results
            with open(daytime_speeds_path, 'w') as f:
                json.dump(daytime_result, f, indent=2)
            
            with open(daytime_stats_path, 'w') as f:
                json.dump(daytime_stats, f, indent=2)
                
            print(f"Successfully processed and saved daytime data for {date}")
            
        except FileNotFoundError:
            print(f"Warning: daytime input file not found for {date}")
        except Exception as e:
            print(f"Error processing daytime data for {date}: {str(e)}")

        # Process nighttime data
        nighttime_input_filename = f'nighttime_speeds_{date}{extension}'
        nighttime_input_path = PROJECT_ROOT / "data" / "output" / nighttime_input_filename
        
        try:
            # Read nighttime input data
            with open(nighttime_input_path, 'r') as f:
                nighttime_input_data = json.load(f)
            
            # Process the nighttime data
            nighttime_result, nighttime_stats = process_coordinate_pairs(nighttime_input_data)
            
            # Print nighttime processing summary
            print(f"\nProcessing Summary for nighttime {date}:")
            print(f"Total pairs: {nighttime_stats['total_pairs']}")
            print(f"Successfully mapped: {nighttime_stats['mapped_pairs']}")
            print(f"Failed to map: {nighttime_stats['failed_pairs']}")
            print(f"Success rate: {(nighttime_stats['mapped_pairs']/nighttime_stats['total_pairs']*100):.2f}%")
            
            print("\nNighttime Segment distribution:")
            nighttime_segment_counts = list(nighttime_stats['segments_per_pair'].values())
            if nighttime_segment_counts:
                print(f"Average segments per pair: {sum(nighttime_segment_counts)/len(nighttime_segment_counts):.2f}")
                print(f"Max segments for a pair: {max(nighttime_segment_counts)}")
                print(f"Min segments for a pair: {min(nighttime_segment_counts)}")
            
            # Build nighttime output paths
            nighttime_speeds_filename = f'osm_way_nighttime_speeds_{date}{extension}'
            nighttime_stats_filename = f'nighttime_mapping_stats_{date}{extension}'
            nighttime_speeds_path = PROJECT_ROOT / "data" / "output" / nighttime_speeds_filename
            nighttime_stats_path = PROJECT_ROOT / "data" / "output" / nighttime_stats_filename
            
            # Save nighttime results
            with open(nighttime_speeds_path, 'w') as f:
                json.dump(nighttime_result, f, indent=2)
            
            with open(nighttime_stats_path, 'w') as f:
                json.dump(nighttime_stats, f, indent=2)
                
            print(f"Successfully processed and saved nighttime data for {date}")
            
        except FileNotFoundError:
            print(f"Warning: nighttime input file not found for {date}")
        except Exception as e:
            print(f"Error processing nighttime data for {date}: {str(e)}")
            
        print(f"{'='*50}\n")

if __name__ == "__main__":
    main()