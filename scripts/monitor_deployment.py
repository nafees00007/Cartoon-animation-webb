#!/usr/bin/env python3
"""
Real-time deployment monitoring with AI-powered anomaly detection
"""

import boto3
import json
import time
import requests
import os
import sys
from datetime import datetime, timedelta
import openai

class DeploymentMonitor:
    def __init__(self, openai_api_key, slack_webhook_url=None):
        self.openai_api_key = openai_api_key
        self.slack_webhook_url = slack_webhook_url
        self.cloudwatch = boto3.client('cloudwatch')
        self.ecs = boto3.client('ecs')
        self.alb = boto3.client('elbv2')
        
        # Monitoring thresholds
        self.thresholds = {
            'error_rate': 5.0,  # 5% error rate
            'cpu_usage': 80.0,  # 80% CPU
            'memory_usage': 85.0,  # 85% memory
            'response_time': 2000,  # 2 seconds
            'latency': 1000  # 1 second
        }
        
        # Baseline metrics (from previous successful deployment)
        self.baseline_metrics = self.get_baseline_metrics()
    
    def get_baseline_metrics(self):
        """Get baseline metrics from previous successful deployment"""
        try:
            end_time = datetime.utcnow() - timedelta(hours=1)
            start_time = end_time - timedelta(hours=1)
            
            # Get baseline error rate
            error_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='HTTPCode_Target_5XX_Count',
                Dimensions=[{'Name': 'LoadBalancer', 'Value': 'cartoon-alb'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            # Get baseline CPU
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ECS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'ServiceName', 'Value': 'cartoon-web-service'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            return {
                'error_rate': error_response['Datapoints'][-1]['Sum'] if error_response['Datapoints'] else 0,
                'cpu_usage': cpu_response['Datapoints'][-1]['Average'] if cpu_response['Datapoints'] else 0
            }
        except Exception as e:
            print(f"Error getting baseline metrics: {e}")
            return {'error_rate': 0, 'cpu_usage': 0}
    
    def get_current_metrics(self):
        """Get current deployment metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            # Error rate
            error_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='HTTPCode_Target_5XX_Count',
                Dimensions=[{'Name': 'LoadBalancer', 'Value': 'cartoon-alb'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            # Response time
            latency_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='TargetResponseTime',
                Dimensions=[{'Name': 'LoadBalancer', 'Value': 'cartoon-alb'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            # CPU usage
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ECS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'ServiceName', 'Value': 'cartoon-web-service'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            # Memory usage
            memory_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ECS',
                MetricName='MemoryUtilization',
                Dimensions=[{'Name': 'ServiceName', 'Value': 'cartoon-web-service'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            return {
                'error_rate': error_response['Datapoints'][-1]['Sum'] if error_response['Datapoints'] else 0,
                'avg_latency': latency_response['Datapoints'][-1]['Average'] if latency_response['Datapoints'] else 0,
                'cpu_usage': cpu_response['Datapoints'][-1]['Average'] if cpu_response['Datapoints'] else 0,
                'memory_usage': memory_response['Datapoints'][-1]['Average'] if memory_response['Datapoints'] else 0,
                'timestamp': end_time.isoformat()
            }
        except Exception as e:
            print(f"Error getting current metrics: {e}")
            return None
    
    def detect_anomalies(self, current_metrics):
        """Detect anomalies using AI analysis"""
        if not current_metrics:
            return None
        
        # Calculate percentage changes from baseline
        error_change = ((current_metrics['error_rate'] - self.baseline_metrics['error_rate']) / 
                       max(self.baseline_metrics['error_rate'], 1)) * 100
        cpu_change = current_metrics['cpu_usage'] - self.baseline_metrics['cpu_usage']
        
        prompt = f"""
        Analyze these deployment metrics for anomalies:
        
        Current Metrics:
        - Error Rate: {current_metrics['error_rate']} (change: {error_change:.1f}%)
        - CPU Usage: {current_metrics['cpu_usage']:.1f}% (change: {cpu_change:.1f}%)
        - Memory Usage: {current_metrics['memory_usage']:.1f}%
        - Avg Latency: {current_metrics['avg_latency']:.1f}ms
        
        Baseline Metrics:
        - Error Rate: {self.baseline_metrics['error_rate']}
        - CPU Usage: {self.baseline_metrics['cpu_usage']:.1f}%
        
        Thresholds:
        - Error Rate: {self.thresholds['error_rate']}%
        - CPU Usage: {self.thresholds['cpu_usage']}%
        - Memory Usage: {self.thresholds['memory_usage']}%
        - Response Time: {self.thresholds['response_time']}ms
        
        Determine:
        1. Are there any anomalies? (YES/NO)
        2. Severity level (LOW/MEDIUM/HIGH/CRITICAL)
        3. Likely causes
        4. Recommended actions
        5. Should we rollback? (YES/NO)
        
        Respond in JSON:
        {{
            "anomaly_detected": true/false,
            "severity": "LOW|MEDIUM|HIGH|CRITICAL",
            "causes": ["cause1", "cause2"],
            "recommendations": ["rec1", "rec2"],
            "rollback_recommended": true/false,
            "confidence": 0.85
        }}
        """
        
        try:
            openai.api_key = self.openai_api_key
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in AI anomaly detection: {e}")
            return None
    
    def check_thresholds(self, metrics):
        """Check if metrics exceed thresholds"""
        alerts = []
        
        if metrics['error_rate'] > self.thresholds['error_rate']:
            alerts.append(f"High error rate: {metrics['error_rate']:.1f}%")
        
        if metrics['cpu_usage'] > self.thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {metrics['cpu_usage']:.1f}%")
        
        if metrics['memory_usage'] > self.thresholds['memory_usage']:
            alerts.append(f"High memory usage: {metrics['memory_usage']:.1f}%")
        
        if metrics['avg_latency'] > self.thresholds['response_time']:
            alerts.append(f"High response time: {metrics['avg_latency']:.1f}ms")
        
        return alerts
    
    def send_alert(self, message, severity="INFO"):
        """Send alert to Slack"""
        if not self.slack_webhook_url:
            print(f"Alert: {message}")
            return
        
        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }
        
        emoji = emoji_map.get(severity, "ℹ️")
        
        slack_message = {
            "text": f"{emoji} **Deployment Alert**\n{message}",
            "username": "Deployment Monitor",
            "icon_emoji": ":robot_face:"
        }
        
        try:
            response = requests.post(self.slack_webhook_url, json=slack_message)
            response.raise_for_status()
        except Exception as e:
            print(f"Error sending Slack alert: {e}")
    
    def rollback_deployment(self):
        """Trigger rollback to previous version"""
        try:
            # Get previous task definition
            task_definitions = self.ecs.list_task_definitions(
                familyPrefix='cartoon-task-definition',
                status='ACTIVE',
                sort='DESC'
            )
            
            if len(task_definitions['taskDefinitionArns']) < 2:
                print("No previous version available for rollback")
                return False
            
            previous_task_def = task_definitions['taskDefinitionArns'][1]
            
            # Update service to previous task definition
            self.ecs.update_service(
                cluster='cartoon-cluster',
                service='cartoon-web-service',
                taskDefinition=previous_task_def
            )
            
            print(f"Rollback initiated to: {previous_task_def}")
            return True
            
        except Exception as e:
            print(f"Error during rollback: {e}")
            return False
    
    def monitor(self, duration_minutes=30):
        """Main monitoring loop"""
        print(f"Starting deployment monitoring for {duration_minutes} minutes...")
        
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while datetime.utcnow() < end_time:
            try:
                # Get current metrics
                metrics = self.get_current_metrics()
                if not metrics:
                    time.sleep(60)
                    continue
                
                print(f"[{datetime.utcnow()}] Monitoring - Error: {metrics['error_rate']:.1f}%, CPU: {metrics['cpu_usage']:.1f}%, Memory: {metrics['memory_usage']:.1f}%")
                
                # Check thresholds
                threshold_alerts = self.check_thresholds(metrics)
                if threshold_alerts:
                    alert_message = "Threshold exceeded:\n" + "\n".join(threshold_alerts)
                    self.send_alert(alert_message, "WARNING")
                
                # AI anomaly detection
                anomaly_analysis = self.detect_anomalies(metrics)
                if anomaly_analysis and anomaly_analysis.get('anomaly_detected'):
                    severity = anomaly_analysis.get('severity', 'MEDIUM')
                    causes = anomaly_analysis.get('causes', [])
                    recommendations = anomaly_analysis.get('recommendations', [])
                    rollback_recommended = anomaly_analysis.get('rollback_recommended', False)
                    
                    alert_message = f"""
Anomaly detected!
Severity: {severity}
Causes: {', '.join(causes)}
Recommendations: {', '.join(recommendations)}
Rollback recommended: {rollback_recommended}
                    """
                    
                    self.send_alert(alert_message, severity)
                    
                    # Auto-rollback for critical issues
                    if severity == "CRITICAL" and rollback_recommended:
                        self.send_alert("🚨 CRITICAL ANOMALY DETECTED - Initiating automatic rollback", "CRITICAL")
                        if self.rollback_deployment():
                            self.send_alert("✅ Rollback completed successfully", "INFO")
                        else:
                            self.send_alert("❌ Rollback failed - Manual intervention required", "CRITICAL")
                        break
                
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("Monitoring stopped by user")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(60)
        
        print("Monitoring completed")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 monitor_deployment.py <duration_minutes> [slack_webhook_url]")
        sys.exit(1)
    
    duration_minutes = int(sys.argv[1])
    slack_webhook_url = sys.argv[2] if len(sys.argv) > 2 else os.getenv('SLACK_WEBHOOK_URL')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    monitor = DeploymentMonitor(openai_api_key, slack_webhook_url)
    monitor.monitor(duration_minutes)

if __name__ == "__main__":
    main()
