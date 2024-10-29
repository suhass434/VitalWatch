import os
import sqlite3
import yaml
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

def load_config():
    with open('config/config.yaml', 'r') as file:
        return yaml.safe_load(file)

class SystemMetrics(Base):
    config = load_config()
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)

class DatabaseHandler:
    def __init__(self):
        self.config = load_config()
        self.engine = create_engine(self.config['database']['url'])
        self.backup_path = self.config['database']['backup_path']
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def store_metrics(self, metrics):
        system_metrics = SystemMetrics(
            cpu_percent=metrics['cpu']['cpu_percent'],
            memory_percent=metrics['memory']['percent'],
            disk_percent=metrics['disk']['percent']
        )
        self.session.add(system_metrics)
        self.session.commit()

    def backup_database(self, backup_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{backup_path}/system_monitor_{timestamp}.db"
        
        os.makedirs(backup_path, exist_ok=True)
        
        backup_connection = sqlite3.connect(backup_file)
        
        with backup_connection:
            self.engine.raw_connection().backup(backup_connection)
        
        return backup_file
    
    def get_historical_metrics(self, limit = 50) {
        metrics = self.session.query(SystemMetrics)\
            .order_by(SystemMetrics.timestamp.desc())\
            .limit(limit)\
            .all()
        return metrics
    }
