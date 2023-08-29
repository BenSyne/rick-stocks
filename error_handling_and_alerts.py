import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import traceback

class ErrorHandler:
    def __init__(self, email_config):
        self.email_config = email_config

    def send_email(self, subject, message):
        msg = MIMEMultipart()
        msg['From'] = self.email_config['from']
        msg['To'] = self.email_config['to']
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
        server.starttls()
        server.login(self.email_config['from'], self.email_config['password'])
        text = msg.as_string()
        server.sendmail(self.email_config['from'], self.email_config['to'], text)
        server.quit()

    def handle_exception(self, e):
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        tb_str = "".join(tb_str)
        print(tb_str)
        self.send_email("Trading System Error", tb_str)

class AlertSystem:
    def __init__(self, email_config):
        self.email_config = email_config

    def send_alert(self, subject, message):
        msg = MIMEMultipart()
        msg['From'] = self.email_config['from']
        msg['To'] = self.email_config['to']
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
        server.starttls()
        server.login(self.email_config['from'], self.email_config['password'])
        text = msg.as_string()
        server.sendmail(self.email_config['from'], self.email_config['to'], text)
        server.quit()

