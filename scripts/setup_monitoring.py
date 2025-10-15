#!/usr/bin/env python3
"""
Setup CloudWatch monitoring and alerting for the deployment
"""

import boto3
import json
import sys
import os
from datetime import datetime, timedelta

class MonitoringSetup:
    def __init__(self, aws_region='us-east-1'):
        self.aws_region = aws_region
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.sns = boto3.client('sns', region_name=aws_region)
        self.ecs = boto3.client('ecs', region_name=aws_region)
        self.alb = boto3.client('elbv2', region_name=aws_region)
    
    def create_dashboard(self, cluster_name, service_name, alb_name):
        """Create CloudWatch dashboard for monitoring"""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/ECS", "CPUUtilization", "ServiceName", service_name, "ClusterName", cluster_name],
                            [".", "MemoryUtilization", ".", ".", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.aws_region,
                        "title": "ECS Service Metrics",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", alb_name],
                            [".", "HTTPCode_Target_2XX_Count", ".", "."],
                            [".", "HTTPCode_Target_4XX_Count", ".", "."],
                            [".", "HTTPCode_Target_5XX_Count", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.aws_region,
                        "title": "ALB Request Metrics",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", alb_name]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.aws_region,
                        "title": "Response Time",
                        "period": 300,
                        "stat": "Average"
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/ApplicationELB", "HealthyHostCount", "LoadBalancer", alb_name],
                            [".", "UnHealthyHostCount", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.aws_region,
                        "title": "Target Health",
                        "period": 300
                    }
                }
            ]
        }
        
        try:
            self.cloudwatch.put_dashboard(
                DashboardName='CartoonAnimationWeb-Dashboard',
                DashboardBody=json.dumps(dashboard_body)
            )
            print("✅ CloudWatch dashboard created successfully")
        except Exception as e:
            print(f"❌ Error creating dashboard: {e}")
    
    def create_alarms(self, cluster_name, service_name, alb_name, sns_topic_arn):
        """Create CloudWatch alarms for monitoring"""
        alarms = [
            {
                'name': 'High-CPU-Utilization',
                'description': 'High CPU utilization for ECS service',
                'metric': 'CPUUtilization',
                'namespace': 'AWS/ECS',
                'dimensions': [
                    {'Name': 'ServiceName', 'Value': service_name},
                    {'Name': 'ClusterName', 'Value': cluster_name}
                ],
                'threshold': 80.0,
                'comparison': 'GreaterThanThreshold',
                'period': 300,
                'evaluation_periods': 2
            },
            {
                'name': 'High-Memory-Utilization',
                'description': 'High memory utilization for ECS service',
                'metric': 'MemoryUtilization',
                'namespace': 'AWS/ECS',
                'dimensions': [
                    {'Name': 'ServiceName', 'Value': service_name},
                    {'Name': 'ClusterName', 'Value': cluster_name}
                ],
                'threshold': 85.0,
                'comparison': 'GreaterThanThreshold',
                'period': 300,
                'evaluation_periods': 2
            },
            {
                'name': 'High-Error-Rate',
                'description': 'High error rate for ALB',
                'metric': 'HTTPCode_Target_5XX_Count',
                'namespace': 'AWS/ApplicationELB',
                'dimensions': [
                    {'Name': 'LoadBalancer', 'Value': alb_name}
                ],
                'threshold': 10.0,
                'comparison': 'GreaterThanThreshold',
                'period': 300,
                'evaluation_periods': 2
            },
            {
                'name': 'High-Response-Time',
                'description': 'High response time for ALB',
                'metric': 'TargetResponseTime',
                'namespace': 'AWS/ApplicationELB',
                'dimensions': [
                    {'Name': 'LoadBalancer', 'Value': alb_name}
                ],
                'threshold': 2000.0,
                'comparison': 'GreaterThanThreshold',
                'period': 300,
                'evaluation_periods': 2
            },
            {
                'name': 'Unhealthy-Targets',
                'description': 'Unhealthy targets in ALB',
                'metric': 'UnHealthyHostCount',
                'namespace': 'AWS/ApplicationELB',
                'dimensions': [
                    {'Name': 'LoadBalancer', 'Value': alb_name}
                ],
                'threshold': 0.0,
                'comparison': 'GreaterThanThreshold',
                'period': 300,
                'evaluation_periods': 1
            }
        ]
        
        for alarm in alarms:
            try:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=f'CartoonAnimationWeb-{alarm["name"]}',
                    AlarmDescription=alarm['description'],
                    MetricName=alarm['metric'],
                    Namespace=alarm['namespace'],
                    Dimensions=alarm['dimensions'],
                    Statistic='Average',
                    Period=alarm['period'],
                    EvaluationPeriods=alarm['evaluation_periods'],
                    Threshold=alarm['threshold'],
                    ComparisonOperator=alarm['comparison'],
                    AlarmActions=[sns_topic_arn],
                    OKActions=[sns_topic_arn],
                    TreatMissingData='notBreaching'
                )
                print(f"✅ Alarm created: {alarm['name']}")
            except Exception as e:
                print(f"❌ Error creating alarm {alarm['name']}: {e}")
    
    def create_log_insights_queries(self):
        """Create CloudWatch Logs Insights queries for common issues"""
        queries = [
            {
                'name': 'Error-Rate-Analysis',
                'query': '''
                fields @timestamp, @message
                | filter @message like /ERROR/ or @message like /error/
                | stats count() by bin(5m)
                | sort @timestamp desc
                '''
            },
            {
                'name': 'Response-Time-Analysis',
                'query': '''
                fields @timestamp, @message
                | filter @message like /response_time/
                | parse @message /response_time=(?<response_time>\\d+)/
                | stats avg(response_time) by bin(5m)
                | sort @timestamp desc
                '''
            },
            {
                'name': 'Memory-Usage-Analysis',
                'query': '''
                fields @timestamp, @message
                | filter @message like /memory/
                | parse @message /memory_usage=(?<memory>\\d+)/
                | stats avg(memory) by bin(5m)
                | sort @timestamp desc
                '''
            }
        ]
        
        for query in queries:
            try:
                # Note: Log Insights queries are typically created manually in the console
                # This is a placeholder for future automation
                print(f"📝 Log Insights query: {query['name']}")
                print(f"Query: {query['query']}")
            except Exception as e:
                print(f"❌ Error with query {query['name']}: {e}")
    
    def setup_monitoring(self, cluster_name, service_name, alb_name, sns_topic_arn):
        """Setup complete monitoring solution"""
        print("🚀 Setting up monitoring for Cartoon Animation Web...")
        
        # Create dashboard
        self.create_dashboard(cluster_name, service_name, alb_name)
        
        # Create alarms
        self.create_alarms(cluster_name, service_name, alb_name, sns_topic_arn)
        
        # Create log insights queries
        self.create_log_insights_queries()
        
        print("✅ Monitoring setup completed!")

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 setup_monitoring.py <cluster_name> <service_name> <alb_name> [sns_topic_arn]")
        sys.exit(1)
    
    cluster_name = sys.argv[1]
    service_name = sys.argv[2]
    alb_name = sys.argv[3]
    sns_topic_arn = sys.argv[4] if len(sys.argv) > 4 else None
    
    if not sns_topic_arn:
        print("⚠️  No SNS topic ARN provided. Alarms will be created but won't send notifications.")
    
    monitor = MonitoringSetup()
    monitor.setup_monitoring(cluster_name, service_name, alb_name, sns_topic_arn)

if __name__ == "__main__":
    main()
