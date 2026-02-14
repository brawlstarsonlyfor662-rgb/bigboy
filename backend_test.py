#!/usr/bin/env python3
"""
Backend Regression Test Suite
Tests the external preview URL endpoints as requested
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://quest-dashboard-4.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, response_data=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def test_healthz(self):
        """Test GET /api/healthz returns 200 {status: ok}"""
        try:
            response = self.session.get(f"{API_BASE}/healthz", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.log_result("GET /api/healthz", True, "Returns 200 with {status: ok}", data)
                    return True
                else:
                    self.log_result("GET /api/healthz", False, f"Wrong response format: {data}")
                    return False
            else:
                self.log_result("GET /api/healthz", False, f"Status code {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("GET /api/healthz", False, f"Request failed: {str(e)}")
            return False
    
    def test_auth_login(self):
        """Test auth login functionality"""
        try:
            # First try to signup a test user
            signup_data = {
                "email": "testuser@example.com",
                "username": "testuser",
                "password": "testpassword123"
            }
            
            # Try signup (might fail if user exists, that's ok)
            signup_response = self.session.post(f"{API_BASE}/auth/signup", json=signup_data, timeout=10)
            
            # Now try login
            login_data = {
                "email": "testuser@example.com", 
                "password": "testpassword123"
            }
            
            login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
            
            if login_response.status_code == 200:
                data = login_response.json()
                if 'access_token' in data and 'user' in data:
                    self.auth_token = data['access_token']
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    self.log_result("Auth Login", True, "Login successful, token received", {'user_id': data['user'].get('id')})
                    return True
                else:
                    self.log_result("Auth Login", False, f"Missing token or user in response: {data}")
                    return False
            else:
                self.log_result("Auth Login", False, f"Login failed with status {login_response.status_code}: {login_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Auth Login", False, f"Auth test failed: {str(e)}")
            return False
    
    def test_tasks_endpoint(self):
        """Test GET /api/tasks returns 200 and respects limit/skip params"""
        if not self.auth_token:
            self.log_result("GET /api/tasks", False, "No auth token available")
            return False
            
        try:
            # Test basic endpoint
            response = self.session.get(f"{API_BASE}/tasks", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("GET /api/tasks (basic)", True, f"Returns 200, got {len(data)} tasks", {'task_count': len(data)})
                
                # Test with limit parameter
                limit_response = self.session.get(f"{API_BASE}/tasks?limit=5", timeout=10)
                if limit_response.status_code == 200:
                    limit_data = limit_response.json()
                    if len(limit_data) <= 5:
                        self.log_result("GET /api/tasks (limit)", True, f"Limit parameter works, got {len(limit_data)} tasks")
                    else:
                        self.log_result("GET /api/tasks (limit)", False, f"Limit not respected, got {len(limit_data)} tasks")
                        return False
                else:
                    self.log_result("GET /api/tasks (limit)", False, f"Limit test failed: {limit_response.status_code}")
                    return False
                
                # Test with skip parameter
                skip_response = self.session.get(f"{API_BASE}/tasks?skip=0&limit=10", timeout=10)
                if skip_response.status_code == 200:
                    self.log_result("GET /api/tasks (skip)", True, "Skip parameter accepted")
                else:
                    self.log_result("GET /api/tasks (skip)", False, f"Skip test failed: {skip_response.status_code}")
                    return False
                    
                return True
            else:
                self.log_result("GET /api/tasks", False, f"Status code {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("GET /api/tasks", False, f"Request failed: {str(e)}")
            return False
    
    def test_analytics_dashboard(self):
        """Test GET /api/analytics/dashboard returns 200 (default) and with ?days=7"""
        if not self.auth_token:
            self.log_result("GET /api/analytics/dashboard", False, "No auth token available")
            return False
            
        try:
            # Test default endpoint
            response = self.session.get(f"{API_BASE}/analytics/dashboard", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['total_tasks', 'current_level', 'discipline_score', 'weekly_data']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("GET /api/analytics/dashboard (default)", True, f"Returns 200 with expected fields", {'window_days': data.get('window_days', 'unknown')})
                else:
                    self.log_result("GET /api/analytics/dashboard (default)", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Test with days=7 parameter
                days_response = self.session.get(f"{API_BASE}/analytics/dashboard?days=7", timeout=10)
                if days_response.status_code == 200:
                    days_data = days_response.json()
                    if days_data.get('window_days') == 7:
                        self.log_result("GET /api/analytics/dashboard (days=7)", True, "Days parameter works correctly")
                    else:
                        self.log_result("GET /api/analytics/dashboard (days=7)", False, f"Days parameter not respected: {days_data.get('window_days')}")
                        return False
                else:
                    self.log_result("GET /api/analytics/dashboard (days=7)", False, f"Days test failed: {days_response.status_code}")
                    return False
                    
                return True
            else:
                self.log_result("GET /api/analytics/dashboard", False, f"Status code {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("GET /api/analytics/dashboard", False, f"Request failed: {str(e)}")
            return False
    
    def test_quests_daily(self):
        """Test GET /api/quests/daily still works"""
        if not self.auth_token:
            self.log_result("GET /api/quests/daily", False, "No auth token available")
            return False
            
        try:
            response = self.session.get(f"{API_BASE}/quests/daily", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'quests' in data and 'date' in data:
                    quest_count = len(data['quests'])
                    self.log_result("GET /api/quests/daily", True, f"Returns 200 with {quest_count} quests", {'date': data['date'], 'quest_count': quest_count})
                    return True
                else:
                    self.log_result("GET /api/quests/daily", False, f"Missing expected fields in response: {data}")
                    return False
            else:
                self.log_result("GET /api/quests/daily", False, f"Status code {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("GET /api/quests/daily", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all regression tests"""
        print(f"🚀 Starting Backend Regression Tests")
        print(f"📍 Testing: {BASE_URL}")
        print("=" * 60)
        
        tests = [
            self.test_healthz,
            self.test_auth_login,
            self.test_tasks_endpoint,
            self.test_analytics_dashboard,
            self.test_quests_daily
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All regression tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) FAILED")
            return False
    
    def print_summary(self):
        """Print detailed test summary"""
        print("\n📋 Detailed Test Summary:")
        print("-" * 40)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            print(f"   {result['message']}")
            if result['response_data']:
                print(f"   Data: {result['response_data']}")
            print()

def main():
    tester = BackendTester()
    success = tester.run_all_tests()
    tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()