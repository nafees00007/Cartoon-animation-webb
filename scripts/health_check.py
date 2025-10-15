#!/usr/bin/env python3
"""
Health check script for the deployed application
"""

import requests
import sys
import time
import json
from datetime import datetime

class HealthChecker:
    def __init__(self, base_url, timeout=10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.endpoints = [
            '/',
            '/health',
            '/api/health'
        ]
    
    def check_endpoint(self, endpoint):
        """Check a specific endpoint"""
        url = f"{self.base_url}{endpoint}"
        try:
            start_time = time.time()
            response = requests.get(url, timeout=self.timeout)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'endpoint': endpoint,
                'status_code': response.status_code,
                'response_time': response_time,
                'success': 200 <= response.status_code < 400,
                'timestamp': datetime.utcnow().isoformat()
            }
        except requests.exceptions.Timeout:
            return {
                'endpoint': endpoint,
                'status_code': None,
                'response_time': self.timeout * 1000,
                'success': False,
                'error': 'Timeout',
                'timestamp': datetime.utcnow().isoformat()
            }
        except requests.exceptions.ConnectionError:
            return {
                'endpoint': endpoint,
                'status_code': None,
                'response_time': None,
                'success': False,
                'error': 'Connection Error',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'endpoint': endpoint,
                'status_code': None,
                'response_time': None,
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def run_health_checks(self):
        """Run all health checks"""
        results = []
        overall_success = True
        
        print(f"🔍 Running health checks for {self.base_url}")
        print("-" * 50)
        
        for endpoint in self.endpoints:
            result = self.check_endpoint(endpoint)
            results.append(result)
            
            if result['success']:
                print(f"✅ {endpoint}: {result['status_code']} ({result['response_time']:.2f}ms)")
            else:
                print(f"❌ {endpoint}: {result.get('error', result['status_code'])}")
                overall_success = False
        
        print("-" * 50)
        
        # Calculate overall metrics
        successful_checks = sum(1 for r in results if r['success'])
        total_checks = len(results)
        avg_response_time = sum(r['response_time'] for r in results if r['response_time']) / max(1, successful_checks)
        
        print(f"📊 Health Check Summary:")
        print(f"   Success Rate: {successful_checks}/{total_checks} ({successful_checks/total_checks*100:.1f}%)")
        print(f"   Average Response Time: {avg_response_time:.2f}ms")
        print(f"   Overall Status: {'✅ HEALTHY' if overall_success else '❌ UNHEALTHY'}")
        
        return {
            'overall_success': overall_success,
            'success_rate': successful_checks / total_checks,
            'avg_response_time': avg_response_time,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def continuous_monitoring(self, interval=60, duration=300):
        """Run continuous health monitoring"""
        print(f"🔄 Starting continuous monitoring for {duration} seconds (checking every {interval}s)")
        
        start_time = time.time()
        check_count = 0
        all_results = []
        
        try:
            while time.time() - start_time < duration:
                check_count += 1
                print(f"\n--- Health Check #{check_count} ---")
                
                result = self.run_health_checks()
                all_results.append(result)
                
                if not result['overall_success']:
                    print("⚠️  Unhealthy status detected!")
                
                if time.time() - start_time < duration:
                    print(f"⏳ Waiting {interval} seconds until next check...")
                    time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        
        # Summary
        total_checks = len(all_results)
        healthy_checks = sum(1 for r in all_results if r['overall_success'])
        avg_success_rate = sum(r['success_rate'] for r in all_results) / total_checks
        avg_response_time = sum(r['avg_response_time'] for r in all_results) / total_checks
        
        print(f"\n📈 Monitoring Summary:")
        print(f"   Total Checks: {total_checks}")
        print(f"   Healthy Checks: {healthy_checks}")
        print(f"   Average Success Rate: {avg_success_rate*100:.1f}%")
        print(f"   Average Response Time: {avg_response_time:.2f}ms")
        
        return all_results

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 health_check.py <base_url> [interval] [duration]")
        print("  base_url: Application URL (e.g., http://example.com)")
        print("  interval: Check interval in seconds (default: 60)")
        print("  duration: Total monitoring duration in seconds (default: 300)")
        sys.exit(1)
    
    base_url = sys.argv[1]
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    
    checker = HealthChecker(base_url)
    
    if duration > 0:
        checker.continuous_monitoring(interval, duration)
    else:
        checker.run_health_checks()

if __name__ == "__main__":
    main()
