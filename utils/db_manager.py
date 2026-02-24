import os
import mysql.connector
from sqlalchemy import create_engine
import pandas as pd

class DBManager:
    def __init__(self):
        # Docker 환경변수 또는 로컬 기본값 사용
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "user")
        self.password = os.getenv("DB_PASSWORD", "password")
        self.database = os.getenv("DB_NAME", "mobility_db")
        
    def get_connection(self):
        """MySQL 연결 객체 반환"""
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def get_engine(self):
        """SQLAlchemy 엔진 반환 (Pandas read_sql 용)"""
        conn_str = f"mysql+mysqlconnector://{self.user}:{self.password}@{self.host}/{self.database}"
        return create_engine(conn_str)

    def fetch_query(self, query):
        """쿼리 결과를 데이터프레임으로 반환"""
        engine = self.get_engine()
        return pd.read_sql(query, engine)

# 싱글톤 패턴으로 인스턴스 제공
db_manager = DBManager()
