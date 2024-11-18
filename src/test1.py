import requests
from datetime import datetime, timedelta

def test_traffic_routing(route_name, start_coords, end_coords, valhalla_url="http://localhost:8002"):
    """
    Test route at different times to verify traffic data integration.
    """
    # Test times: midnight (freeflow), 8am (rush hour), 2pm (mid-day), 5pm (evening rush)
    test_times = ["00:00", "08:00", "14:00", "17:00"]
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    results = {}
    
    for time in test_times:
        request_json = {
            "locations": [
                {"lat": start_coords[0], "lon": start_coords[1]},
                {"lat": end_coords[0], "lon": end_coords[1]}
            ],
            "costing": "auto",
            "date_time": {
                "type": 1,  # departure time
                "value": f"{current_date}T{time}"
            }
        }
        
        try:
            response = requests.post(f"{valhalla_url}/route", json=request_json)
            response.raise_for_status()
            data = response.json()
            
            # Extract time and distance
            time_sec = data['trip']['summary']['time']
            distance_km = data['trip']['summary']['length']
            
            # Calculate average speed
            avg_speed_kmh = (distance_km / time_sec) * 3600
            
            results[time] = {
                "time_seconds": time_sec,
                "distance_km": distance_km,
                "avg_speed_kmh": avg_speed_kmh
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error at {time}: {e}")
            results[time] = None
    
    return results

def main():
    # Test routes in Amman
    routes = {
        "City Center to Airport": {
            "start": (31.9539, 35.9284),  # Downtown Amman
            "end": (31.7225, 35.9932)     # Queen Alia International Airport
        },
        "West to East Amman": {
            "start": (31.9572, 35.8659),  # 8th Circle area
            "end": (31.9861, 35.9870)     # East Amman
        },
        "University Route": {
            "start": (31.9455, 35.9283),  # University of Jordan
            "end": (31.8975, 35.8730)     # Sport City Circle
        }
    }
    
    print("Testing traffic routing in Amman...")
    print("=" * 60)
    
    for route_name, coords in routes.items():
        print(f"\nTesting route: {route_name}")
        print("-" * 60)
        
        results = test_traffic_routing(route_name, coords["start"], coords["end"])
        
        for time, data in results.items():
            if data:
                print(f"\nTime of day: {time}")
                print(f"Journey time: {data['time_seconds']/60:.1f} minutes")
                print(f"Distance: {data['distance_km']:.1f} km")
                print(f"Average speed: {data['avg_speed_kmh']:.1f} km/h")
            else:
                print(f"\nTime of day: {time} - Failed to get route")
                
        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()