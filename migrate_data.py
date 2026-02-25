import pandas as pd
import sys
import traceback
import MySQLdb

# Add path so utils can be imported
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.db_manager import db_manager

def migrate():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # 0. 핵심 테이블 전체 초기화 (없는 경우에만 생성)
        print('Initializing missing core tables...')
        
        # faq_data 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question TEXT,
                answer TEXT,
                category VARCHAR(255),
                source VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # charging_stations 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS charging_stations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                station_id VARCHAR(100) UNIQUE,
                name VARCHAR(255),
                address VARCHAR(255),
                lat FLOAT,
                lng FLOAT,
                fast_count INT DEFAULT 0,
                slow_count INT DEFAULT 0,
                operator VARCHAR(100),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # regional_ev_status 기본 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regional_ev_status (
                id INT AUTO_INCREMENT PRIMARY KEY,
                region VARCHAR(100),
                year INT,
                count_ev INT,
                count_charger INT DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_region_year (region, year)
            )
        ''')
        conn.commit()

        # 1. regional_ev_status 테이블에 count_ice 열 추가 (일반차 데이터용 컬럼)
        try:
            cursor.execute("SHOW COLUMNS FROM regional_ev_status LIKE 'count_ice'")
            if not cursor.fetchone():
                print('Adding count_ice column to regional_ev_status...')
                cursor.execute('ALTER TABLE regional_ev_status ADD COLUMN count_ice INT DEFAULT 0')
                conn.commit()
        except Exception as e:
            print('Error checking/adding count_ice column:', e)

        # 통합 CSV 읽어서 count_ice 업데이트
        print('Migrating regional_ev_status data...')
        df_main = pd.read_csv('전기차_일반차_통합.csv', encoding='utf-8-sig')
        for _, row in df_main.iterrows():
            region = row['region']
            year = int(row['year'])
            count_ice = int(row['일반차'])
            
            cursor.execute('''
                UPDATE regional_ev_status
                SET count_ice = %s
                WHERE region = %s AND year = %s
            ''', (count_ice, region, year))
            
            # 만약 반영된 행이 0이라면 INSERT를 합니다.
            if cursor.rowcount == 0:
                count_ev = int(row['count_ev'])
                cursor.execute('''
                    INSERT INTO regional_ev_status (region, year, count_ev, count_charger, count_ice)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (region, year, count_ev, 0, count_ice))
        
        conn.commit()
        print('Migrated count_ice to regional_ev_status.')

        # 2. regional_fuel_status 테이블 생성 및 데이터 삽입
        print('Migrating regional_fuel_status data...')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regional_fuel_status (
                id INT AUTO_INCREMENT PRIMARY KEY,
                region VARCHAR(50),
                year INT,
                fuel_type VARCHAR(50),
                count INT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_regional_fuel (region, year, fuel_type)
            )
        ''')
        conn.commit()
        
        df_fuel = pd.read_csv('지역별_연료별_등록대수_최종.csv', encoding='utf-8-sig')
        for _, row in df_fuel.iterrows():
            region = row['지역']
            year = int(row['연도']) if pd.notna(row['연도']) else 0
            fuel_type = row['연료']
            count = int(row['대수'])
            
            cursor.execute('''
                INSERT INTO regional_fuel_status (region, year, fuel_type, count)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE count=VALUES(count)
            ''', (region, year, fuel_type, count))
        
        conn.commit()
        print('Migrated regional_fuel_status.')

        # 3. ev_subsidy_status 테이블 생성 및 데이터 삽입
        print('Migrating ev_subsidy_status data...')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ev_subsidy_status (
                id INT AUTO_INCREMENT PRIMARY KEY,
                region VARCHAR(50),
                category VARCHAR(100),
                amount INT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_region_category (region, category)
            )
        ''')
        conn.commit()

        try:
            df_subsidy = pd.read_csv('전기차보조금_tidy.csv', encoding='utf-8-sig')
        except:
            df_subsidy = pd.read_csv('전기차보조금_tidy.csv', encoding='cp949')
            
        for _, row in df_subsidy.iterrows():
            region = row['지역']
            category = row['보조금항목']
            amount = int(row['금액'])
            
            cursor.execute('''
                INSERT INTO ev_subsidy_status (region, category, amount)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE amount=VALUES(amount)
            ''', (region, category, amount))
            
        conn.commit()
        print('Migrated ev_subsidy_status_data.')
        
        cursor.close()
        conn.close()
        print('All database migrations completed successfully!')

    except Exception as e:
        print('Failed migration:', e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    migrate()
