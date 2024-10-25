import streamlit as st
import plotly.graph_objects as go
from src.database.db_handler import DatabaseHandler
import pandas as pd

def main():
    st.title("System Health Monitor Dashboard")
    
    db = DatabaseHandler()
    
    # Get latest metrics
    metrics = pd.read_sql('SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 100', 
                         db.engine)
    
    # CPU Usage Graph
    fig_cpu = go.Figure()
    fig_cpu.add_trace(go.Scatter(x=metrics['timestamp'], 
                                y=metrics['cpu_percent'],
                                mode='lines',
                                name='CPU Usage'))
    st.plotly_chart(fig_cpu)
    
    # Memory Usage Graph
    fig_mem = go.Figure()
    fig_mem.add_trace(go.Scatter(x=metrics['timestamp'], 
                                y=metrics['memory_percent'],
                                mode='lines',
                                name='Memory Usage'))
    st.plotly_chart(fig_mem)
    
    # Recent Alerts
    st.subheader("Recent Alerts")
    # Add code to display recent alerts from database

if __name__ == "__main__":
    main()