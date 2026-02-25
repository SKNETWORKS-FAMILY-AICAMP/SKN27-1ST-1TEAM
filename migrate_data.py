import pandas as pd
import sys
import traceback
import os
import glob
from sqlalchemy import text

# Add path so utils can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.db_manager import db_manager

def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def migrate():
    try:
        engine = db_manager.get_engine()
        print('Connected to database engine.')

        # Mapping of tables to their CSV patterns
        table_config = {
            'faq_data': 'faq_data_*.csv',
            'charging_stations': 'charging_stations_*.csv',
            'regional_ev_status': 'regional_ev_status_*.csv',
            'regional_fuel_status': 'regional_fuel_status_*.csv',
            'ev_subsidy_status': 'ev_subsidy_status_*.csv'
        }

        # 0. Table Definitions (Ensuring tables exist)
        with engine.connect() as conn:
            print('Initializing tables...')
            # faq_data
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS faq_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question TEXT,
                    answer TEXT,
                    category VARCHAR(255),
                    source VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            
            # charging_stations
            conn.execute(text('''
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
            '''))
            
            # regional_ev_status
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS regional_ev_status (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    region VARCHAR(100),
                    year INT,
                    count_ev INT,
                    count_charger INT DEFAULT 0,
                    count_ice INT DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_region_year (region, year)
                )
            '''))

            # regional_fuel_status
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS regional_fuel_status (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    region VARCHAR(50),
                    year INT,
                    fuel_type VARCHAR(50),
                    count INT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_regional_fuel (region, year, fuel_type)
                )
            '''))

            # ev_subsidy_status
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS ev_subsidy_status (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    region VARCHAR(50),
                    category VARCHAR(100),
                    amount INT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_region_category (region, category)
                )
            '''))
            conn.commit()

        # 1. Migrate Data
        for table_name, pattern in table_config.items():
            file_path = get_latest_file(pattern)
            if not file_path:
                print(f"Warning: No file found for pattern {pattern}. Skipping table {table_name}.")
                continue
            
            print(f"Migrating {file_path} to {table_name}...")
            df = pd.read_csv(file_path)
            
            # If the CSV has an 'id' column, we might want to drop it to let the DB handle auto-increment
            # OR keep it if we want exact IDs. Given '그대로' (as is), let's keep it but handle duplicates.
            
            # To handle '그대로' and avoid duplicates, we can truncate before insert
            with engine.connect() as conn:
                conn.execute(text(f"SET FOREIGN_KEY_CHECKS = 0;"))
                conn.execute(text(f"TRUNCATE TABLE {table_name};"))
                conn.execute(text(f"SET FOREIGN_KEY_CHECKS = 1;"))
                conn.commit()
            
            # Use to_sql for fast insertion
            df.to_sql(table_name, engine, if_exists='append', index=False)
            print(f"Successfully migrated {len(df)} rows to {table_name}.")

        print('All database migrations completed successfully!')

    except Exception as e:
        print('Failed migration:', e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    migrate()
