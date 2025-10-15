#!/usr/bin/env python3
"""
AI Analysis Script for PR, Testing, and Deployment
"""

import openai
import json
import sys
import os
import boto3
from datetime import datetime, timedelta
import subprocess

class AIAnalyzer:
    def __init__(self, openai_api_key):
        openai.api_key = openai_api_key
        self.cloudwatch = boto3.client('cloudwatch')
        self.ecs = boto3.client('ecs')
        self.ecr = boto3.client('ecr')
    
    def analyze_pr_changes(self, diff_content, changed_files):
        """Analyze PR changes for risk assessment"""
        prompt = f"""
        Analyze this code diff and provide:
        1. A concise summary of changes (max 100 words)
        2. Risk level: LOW, MEDIUM, or HIGH
        3. Specific risky areas to watch
        4. Recommended testing focus
        
        Changed files: {changed_files}
        
        Diff:
        {diff_content}
        
        Respond in JSON format:
        {{
            "summary": "string",
            "risk_level": "LOW|MEDIUM|HIGH",
            "risky_areas": ["area1", "area2"],
            "testing_focus": ["test1", "test2"]
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in PR analysis: {e}")
            return {
                "summary": "Analysis failed",
                "risk_level": "UNKNOWN",
                "risky_areas": [],
                "testing_focus": []
            }
    
    def analyze_test_results(self, test_logs):
        """Analyze test results and provide insights"""
        prompt = f"""
        Analyze these test results and provide:
        1. Human-readable summary of test status
        2. Specific failures and likely causes
        3. Recommendations for fixes
        4. Overall test health score (1-10)
        
        Test logs:
        {test_logs}
        
        Respond in JSON format:
        {{
            "summary": "string",
            "failures": ["failure1", "failure2"],
            "recommendations": ["rec1", "rec2"],
            "health_score": 8
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in test analysis: {e}")
            return {
                "summary": "Test analysis failed",
                "failures": [],
                "recommendations": [],
                "health_score": 5
            }
    
    def analyze_deployment_risk(self, pr_summary, risk_level, image_tag):
        """Analyze deployment risk and recommend strategy"""
        # Get recent metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        try:
            # Get error rate
            error_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='HTTPCode_Target_5XX_Count',
                Dimensions=[{'Name': 'LoadBalancer', 'Value': 'cartoon-alb'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            error_rate = error_response['Datapoints'][-1]['Sum'] if error_response['Datapoints'] else 0
            
            # Get CPU usage
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ECS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'ServiceName', 'Value': 'cartoon-web-service'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            cpu_usage = cpu_response['Datapoints'][-1]['Average'] if cpu_response['Datapoints'] else 0
            
        except Exception as e:
            print(f"Error getting metrics: {e}")
            error_rate = 0
            cpu_usage = 0
        
        prompt = f"""
        Analyze deployment risk based on:
        1. Recent error rates: {error_rate}
        2. CPU usage: {cpu_usage}%
        3. PR risk level: {risk_level}
        4. Change summary: {pr_summary}
        5. Image tag: {image_tag}
        
        Recommend:
        1. Deployment strategy: CANARY or FULL_ROLLOUT
        2. Risk mitigation steps
        3. Monitoring focus areas
        4. Rollback threshold (error rate %)
        
        Respond in JSON:
        {{
            "strategy": "CANARY|FULL_ROLLOUT",
            "risk_mitigation": ["step1", "step2"],
            "monitoring_focus": ["metric1", "metric2"],
            "rollback_threshold": 5.0
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in deployment analysis: {e}")
            return {
                "strategy": "FULL_ROLLOUT",
                "risk_mitigation": ["Monitor closely"],
                "monitoring_focus": ["error_rate", "cpu_usage"],
                "rollback_threshold": 5.0
            }
    
    def generate_deployment_summary(self, image_tag, deployment_time, metrics):
        """Generate AI-powered deployment summary"""
        prompt = f"""
        Generate a deployment summary report based on:
        
        Deployment: {image_tag}
        Time: {deployment_time}
        Error Rate: {metrics.get('error_rate', 0)}
        Avg Latency: {metrics.get('avg_latency', 0)}ms
        CPU Usage: {metrics.get('cpu_usage', 0)}%
        Memory Usage: {metrics.get('memory_usage', 0)}%
        
        Provide:
        1. Deployment status (SUCCESS/WARNING/FAILED)
        2. Key metrics summary
        3. Performance comparison to previous deployment
        4. Recommendations for monitoring
        5. Any alerts or concerns
        6. Next steps
        
        Format as a professional deployment report suitable for Slack/Teams.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating deployment summary: {e}")
            return f"Deployment {image_tag} completed at {deployment_time}. Metrics: {metrics}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ai_analysis.py <analysis_type> [args...]")
        sys.exit(1)
    
    analysis_type = sys.argv[1]
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    analyzer = AIAnalyzer(openai_api_key)
    
    if analysis_type == "pr":
        if len(sys.argv) < 4:
            print("Usage: python3 ai_analysis.py pr <diff_file> <changed_files>")
            sys.exit(1)
        
        with open(sys.argv[2], 'r') as f:
            diff_content = f.read()
        
        with open(sys.argv[3], 'r') as f:
            changed_files = f.read()
        
        result = analyzer.analyze_pr_changes(diff_content, changed_files)
        print(json.dumps(result))
    
    elif analysis_type == "test":
        if len(sys.argv) < 3:
            print("Usage: python3 ai_analysis.py test <test_log_file>")
            sys.exit(1)
        
        with open(sys.argv[2], 'r') as f:
            test_logs = f.read()
        
        result = analyzer.analyze_test_results(test_logs)
        print(json.dumps(result))
    
    elif analysis_type == "deploy":
        if len(sys.argv) < 5:
            print("Usage: python3 ai_analysis.py deploy <pr_summary> <risk_level> <image_tag>")
            sys.exit(1)
        
        pr_summary = sys.argv[2]
        risk_level = sys.argv[3]
        image_tag = sys.argv[4]
        
        result = analyzer.analyze_deployment_risk(pr_summary, risk_level, image_tag)
        print(json.dumps(result))
    
    elif analysis_type == "summary":
        if len(sys.argv) < 4:
            print("Usage: python3 ai_analysis.py summary <image_tag> <deployment_time> <metrics_json>")
            sys.exit(1)
        
        image_tag = sys.argv[2]
        deployment_time = sys.argv[3]
        metrics = json.loads(sys.argv[4])
        
        result = analyzer.generate_deployment_summary(image_tag, deployment_time, metrics)
        print(result)
    
    else:
        print(f"Unknown analysis type: {analysis_type}")
        sys.exit(1)

if __name__ == "__main__":
    main()
