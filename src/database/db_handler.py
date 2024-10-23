from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class SystemMetrics(Base):
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)

class DatabaseHandler:
    def __init__(self, db_url='sqlite:///system_monitor.db'):
        self.engine = create_engine(db_url)
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