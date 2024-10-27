import smtplib
from email.mime.text import MIMEText
import requests
import streamlit as st
class AlertManager:
    def __init__(self, config):
        self.config = config
        self.alert_channels = {
            'email': self.send_email_alert,
            'slack': self.send_slack_alert
        }
    
    def send_email_alert(self, subject, message):
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = self.config['email']['from']
        msg['To'] = self.config['email']['to']
        
        try:
            with smtplib.SMTP(self.config['email']['smtp_server']) as server:
                server.login(self.config['email']['username'], 
                           self.config['email']['password'])
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def send_slack_alert(self, message):
        try:
            response = requests.post(
                self.config['slack']['webhook_url'],
                json={'text': message}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Slack alert: {str(e)}")
            return False