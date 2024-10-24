import numpy as np
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1)
        self.trained = False
    
    def train(self, historical_data):
        if len(historical_data) > 100:
            self.model.fit(historical_data)
            self.trained = True
    
    def detect_anomalies(self, current_metrics):
        if not self.trained:
            return False
        
        prediction = self.model.predict([[
            current_metrics['cpu']['cpu_percent'],
            current_metrics['memory']['percent'],
            current_metrics['disk']['percent']
        ]])
        return prediction[0] == -1

        detector = AnomalyDetector()