import os
import sys
import requests
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_manager import db_manager

def sync_from_bigdata_api(api_key="zpFgaa8WF7BcRDcvJ9mI1JSf7D6f0YFTu04M4908"):
    """한전 빅데이터 API를 통해 주요 지역 충전소 정보 동기화"""
    print(f"Fetching data from KEPCO Big Data API (Key: {api_key[:5]}...)...")
    
    # 주요 광역시/도 코드
    metro_codes = ["11", "41", "26", "27", "28", "29", "30", "31", "36"]
    base_url = "https://bigdata.kepco.co.kr/openapi/v1/EVcharge.do"
    
    # 브라우저 헤더를 최대한 비슷하게 구성
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://bigdata.kepco.co.kr/",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    
    total_count = 0
    
    for metro in metro_codes:
        print(f"Fetching Metro Code: {metro}...")
        params = {
            "metroCd": metro,
            "apiKey": api_key,
            "returnType": "json"
        }
        
        try:
            # 401 에러 방지를 위해 세션 유지 시도 (필요한 경우)
            response = requests.get(base_url, params=params, headers=headers, verify=False, timeout=20)
            
            if response.status_code != 200:
                print(f"API Error for {metro}: {response.status_code}, {response.text[:100]}")
                continue
                
            data = response.json()
            stations = data.get("data", [])
            
            if not stations:
                print(f"No data or invalid response for metro {metro}: {data}")
                continue

            print(f"Found {len(stations)} stations in metro {metro}. Updating database...")
            
            for st in stations:
                # 필드명 매핑 (stnPlace -> name, stnAddr -> address, rapidCnt -> fast_count, slowCnt -> slow_count)
                name = st.get("stnPlace", "Unknown")
                address = st.get("stnAddr", "")
                
                import hashlib
                station_id = hashlib.md5(f"{name}{address}".encode()).hexdigest()
                
                # 빅데이터 API는 현재 좌표(lat, lng)를 주지 않으므로 ArcGIS로 지오코딩 시도
                lat = 0.0
                lng = 0.0
                
                try:
                    import urllib.parse
                    clean_addr = address.split('(')[0].split(',')[0].strip()
                    g_url = f'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?singleLine={urllib.parse.quote(clean_addr)}&f=json&maxLocations=1'
                    g_res = requests.get(g_url, timeout=3)
                    if g_res.status_code == 200:
                        cands = g_res.json().get('candidates', [])
                        if cands:
                            loc = cands[0].get('location', {})
                            lat, lng = loc.get('y', 0.0), loc.get('x', 0.0)
                except Exception:
                    pass
                
                fast_count = st.get("rapidCnt", 0)
                slow_count = st.get("slowCnt", 0)
                operator = "한전(빅데이터)"
                
                db_manager.execute_query(
                    """
                    INSERT INTO charging_stations 
                    (station_id, name, address, lat, lng, fast_count, slow_count, operator) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    name=VALUES(name), address=VALUES(address), 
                    fast_count=VALUES(fast_count), slow_count=VALUES(slow_count)
                    """,
                    (station_id, name, address, lat, lng, fast_count, slow_count, operator)
                )
                total_count += 1
                
        except Exception as e:
            print(f"Failed to fetch metro {metro}: {e}")
            
    print(f"Successfully synced a total of {total_count} stations from Big Data API.")

if __name__ == "__main__":
    # 사용자로부터 API Key를 인자로 받거나 기본값 사용
    user_key = sys.argv[1] if len(sys.argv) > 1 else "zpFgaa8WF7BcRDcvJ9mI1JSf7D6f0YFTu04M4908"
    sync_from_bigdata_api(user_key)
