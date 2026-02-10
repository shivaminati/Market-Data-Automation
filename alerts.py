"""
Alerts Module
Monitors price thresholds and triggers notifications
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime
from config import Config

# Configure logging
logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages price alerts and notifications
    """
    
    def __init__(self):
        """Initialize alert manager"""
        self.thresholds = Config.ALERT_THRESHOLDS
        self.email_enabled = Config.ENABLE_EMAIL_ALERTS
        
        logger.info(f"Alert Manager initialized with {len(self.thresholds)} threshold configurations")
        
        if self.email_enabled:
            logger.info("Email alerts are ENABLED")
        else:
            logger.info("Email alerts are DISABLED (console only)")
    
    def check_thresholds(self, quote_data: Dict) -> List[Dict]:
        """
        Check if a quote triggers any alerts
        
        Args:
            quote_data: Dictionary with quote information
        
        Returns:
            List of triggered alerts
        """
        symbol = quote_data.get('symbol')
        price = quote_data.get('price')
        
        if not symbol or price is None:
            return []
        
        # Check if this symbol has thresholds configured
        if symbol not in self.thresholds:
            return []
        
        thresholds = self.thresholds[symbol]
        alerts = []
        
        # Check minimum threshold
        if thresholds.get('min') is not None:
            if price < thresholds['min']:
                alert = {
                    'symbol': symbol,
                    'current_price': price,
                    'threshold_type': 'BELOW_MINIMUM',
                    'threshold_value': thresholds['min'],
                    'message': f"🔴 ALERT: {symbol} fell below ${thresholds['min']:.2f}! Current: ${price:.2f}",
                    'timestamp': quote_data.get('timestamp', datetime.utcnow().isoformat()),
                    'severity': 'HIGH'
                }
                alerts.append(alert)
                logger.warning(alert['message'])
        
        # Check maximum threshold
        if thresholds.get('max') is not None:
            if price > thresholds['max']:
                alert = {
                    'symbol': symbol,
                    'current_price': price,
                    'threshold_type': 'ABOVE_MAXIMUM',
                    'threshold_value': thresholds['max'],
                    'message': f"🟢 ALERT: {symbol} exceeded ${thresholds['max']:.2f}! Current: ${price:.2f}",
                    'timestamp': quote_data.get('timestamp', datetime.utcnow().isoformat()),
                    'severity': 'HIGH'
                }
                alerts.append(alert)
                logger.warning(alert['message'])
        
        return alerts
    
    def check_multiple(self, quotes: List[Dict]) -> List[Dict]:
        """
        Check thresholds for multiple quotes
        
        Args:
            quotes: List of quote dictionaries
        
        Returns:
            List of all triggered alerts
        """
        all_alerts = []
        
        for quote in quotes:
            alerts = self.check_thresholds(quote)
            all_alerts.extend(alerts)
        
        if all_alerts:
            logger.info(f"Triggered {len(all_alerts)} alerts")
        
        return all_alerts
    
    def send_alerts(self, alerts: List[Dict]):
        """
        Send alerts via configured channels
        
        Args:
            alerts: List of alert dictionaries
        """
        if not alerts:
            return
        
        # Always send console alerts
        self._send_console_alerts(alerts)
        
        # Send email alerts if enabled
        if self.email_enabled:
            try:
                self._send_email_alerts(alerts)
            except Exception as e:
                logger.error(f"Failed to send email alerts: {e}")
    
    def _send_console_alerts(self, alerts: List[Dict]):
        """
        Print alerts to console
        
        Args:
            alerts: List of alert dictionaries
        """
        print("\n" + "="*70)
        print("🚨 PRICE ALERTS TRIGGERED 🚨")
        print("="*70)
        
        for alert in alerts:
            print(f"\n{alert['message']}")
            print(f"   Time: {alert['timestamp']}")
            print(f"   Threshold: ${alert['threshold_value']:.2f}")
            print(f"   Type: {alert['threshold_type']}")
        
        print("\n" + "="*70 + "\n")
    
    def _send_email_alerts(self, alerts: List[Dict]):
        """
        Send alerts via email
        
        Args:
            alerts: List of alert dictionaries
        """
        if not all([Config.SMTP_USERNAME, Config.SMTP_PASSWORD, Config.ALERT_EMAIL_TO]):
            logger.error("Email configuration incomplete. Cannot send email alerts.")
            return
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 Market Alert: {len(alerts)} Price Threshold(s) Crossed"
            msg['From'] = Config.SMTP_USERNAME
            msg['To'] = Config.ALERT_EMAIL_TO
            
            # Create email body
            text_body = self._create_text_email_body(alerts)
            html_body = self._create_html_email_body(alerts)
            
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email alert sent successfully to {Config.ALERT_EMAIL_TO}")
        
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    def _create_text_email_body(self, alerts: List[Dict]) -> str:
        """
        Create plain text email body
        
        Args:
            alerts: List of alert dictionaries
        
        Returns:
            Plain text email body
        """
        body = "MARKET PRICE ALERTS\n"
        body += "=" * 50 + "\n\n"
        
        for alert in alerts:
            body += f"Symbol: {alert['symbol']}\n"
            body += f"Current Price: ${alert['current_price']:.2f}\n"
            body += f"Alert Type: {alert['threshold_type']}\n"
            body += f"Threshold: ${alert['threshold_value']:.2f}\n"
            body += f"Time: {alert['timestamp']}\n"
            body += "-" * 50 + "\n\n"
        
        body += f"\nTotal Alerts: {len(alerts)}\n"
        body += f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        return body
    
    def _create_html_email_body(self, alerts: List[Dict]) -> str:
        """
        Create HTML email body
        
        Args:
            alerts: List of alert dictionaries
        
        Returns:
            HTML email body
        """
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .header { background-color: #f44336; color: white; padding: 20px; text-align: center; }
                .alert-box { background-color: #f9f9f9; border-left: 5px solid #f44336; margin: 20px 0; padding: 15px; }
                .alert-high { border-left-color: #f44336; }
                .alert-medium { border-left-color: #ff9800; }
                .price { font-size: 24px; font-weight: bold; color: #333; }
                .footer { margin-top: 30px; padding: 20px; background-color: #f0f0f0; text-align: center; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Market Price Alerts</h1>
            </div>
        """
        
        for alert in alerts:
            severity_class = 'alert-high' if alert['severity'] == 'HIGH' else 'alert-medium'
            
            html += f"""
            <div class="alert-box {severity_class}">
                <h2>{alert['symbol']}</h2>
                <p class="price">Current Price: ${alert['current_price']:.2f}</p>
                <p><strong>Alert Type:</strong> {alert['threshold_type'].replace('_', ' ').title()}</p>
                <p><strong>Threshold:</strong> ${alert['threshold_value']:.2f}</p>
                <p><strong>Time:</strong> {alert['timestamp']}</p>
            </div>
            """
        
        html += f"""
            <div class="footer">
                <p>Total Alerts: {len(alerts)}</p>
                <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p>Market Data Automation Tool</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def get_threshold_summary(self) -> str:
        """
        Get a summary of configured thresholds
        
        Returns:
            Formatted string with threshold information
        """
        if not self.thresholds:
            return "No thresholds configured"
        
        summary = "\n📊 CONFIGURED PRICE THRESHOLDS\n"
        summary += "="*50 + "\n\n"
        
        for symbol, thresholds in self.thresholds.items():
            summary += f"{symbol}:\n"
            if thresholds.get('min'):
                summary += f"  🔴 Alert if below: ${thresholds['min']:.2f}\n"
            if thresholds.get('max'):
                summary += f"  🟢 Alert if above: ${thresholds['max']:.2f}\n"
            summary += "\n"
        
        return summary


# Convenience function
def check_and_alert(quotes: List[Dict]) -> List[Dict]:
    """
    Convenience function to check quotes and send alerts
    
    Args:
        quotes: List of quote dictionaries
    
    Returns:
        List of triggered alerts
    """
    manager = AlertManager()
    alerts = manager.check_multiple(quotes)
    
    if alerts:
        manager.send_alerts(alerts)
    
    return alerts
