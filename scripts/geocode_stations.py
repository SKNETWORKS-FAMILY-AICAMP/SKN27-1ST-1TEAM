import os
import sys
import threading
import time
import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_manager import db_manager

def get_coordinates(address):
    """ArcGIS REST API를 사용하여 주소를 좌표로 변환"""
    # 주소 정제 (괄호 안의 내용 제거 등 상세 주소 제거)
    clean_addr = address.split('(')[0].split(',')[0].strip()
    
    url = f'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?singleLine={urllib.parse.quote(clean_addr)}&f=json&maxLocations=1'
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get('candidates', [])
            if candidates:
                loc = candidates[0].get('location', {})
                return loc.get('y', 0.0), loc.get('x', 0.0)
    except Exception as e:
        pass
    
    # 너무 구체적인 주소에서 실패한 경우 좀 더 넓은 주소로 재시도
    parts = clean_addr.split()
    if len(parts) > 2:
        shorter_addr = " ".join(parts[:3]) # e.g. 서울특별시 강남구 자곡동
        url = f'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?singleLine={urllib.parse.quote(shorter_addr)}&f=json&maxLocations=1'
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get('candidates', [])
                if candidates:
                    loc = candidates[0].get('location', {})
                    return loc.get('y', 0.0), loc.get('x', 0.0)
        except Exception:
            pass
            
    return 0.0, 0.0

def process_station(station):
    station_id, address = station
    lat, lng = get_coordinates(address)
    
    if lat != 0.0 and lng != 0.0:
        db_manager.execute_query(
            "UPDATE charging_stations SET lat = %s, lng = %s WHERE station_id = %s",
            (lat, lng, station_id)
        )
        return True
    return False

def main():
    print("Fetching stations without coordinates...")
    df = db_manager.fetch_query("SELECT station_id, address FROM charging_stations WHERE lat = 0.0 OR lng = 0.0")
    
    if df.empty:
        print("All stations have coordinates.")
        return
        
    stations = list(df.itertuples(index=False, name=None))
    total = len(stations)
    print(f"Found {total} stations to geocode.")
    
    success_count = 0
    
    start_time = time.time()
    # 5개의 스레드로 병행 처리
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(process_station, stations)
        
        for i, success in enumerate(results):
            if success:
                success_count += 1
            
            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/{total} (Success: {success_count})")
                
    end_time = time.time()
    print(f"Finished geocoding! Successfully updated {success_count}/{total} stations in {end_time - start_time:.1f} seconds.")

if __name__ == "__main__":
    main()
