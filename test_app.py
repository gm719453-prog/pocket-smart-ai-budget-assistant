import unittest
import json
from app import app
from database import query_db, execute_db

class PocketSmartTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # Clean test user if exists
        execute_db("DELETE FROM users WHERE email = %s", ("teststudent@example.com",))

    def tearDown(self):
        execute_db("DELETE FROM users WHERE email = %s", ("teststudent@example.com",))

    def test_01_landing_page(self):
        """Test landing page loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pocket", response.data)
        self.assertIn(b"Take Control of", response.data)

    def test_02_registration_and_login(self):
        """Test user registration and subsequent login."""
        # 1. Sign Up
        res = self.client.post('/signup', data={
            'name': 'Test Student',
            'email': 'teststudent@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dashboard", res.data)

        # 2. Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        self.assertIn(b"LOGIN", res_logout.data)

        # 3. Login
        res_login = self.client.post('/login', data={
            'email': 'teststudent@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b"Dashboard", res_login.data)

    def test_03_expenses_and_budget_lifecycle(self):
        """Test full financial cycle: income, expenses, budgets, savings."""
        # Sign up
        self.client.post('/signup', data={
            'name': 'Budget Master',
            'email': 'teststudent@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # Update Income
        res_inc = self.client.post('/income/update', data={'income': '30000'}, follow_redirects=True)
        self.assertEqual(res_inc.status_code, 200)

        # Add Expense
        res_exp = self.client.post('/expenses/add', data={
            'amount': '1500',
            'category': 'Food',
            'description': 'Team Dinner',
            'expense_date': '2026-10-01'
        }, follow_redirects=True)
        self.assertEqual(res_exp.status_code, 200)
        self.assertIn(b"Expense added successfully", res_exp.data)

        # Add Budget
        res_bud = self.client.post('/budget/add', data={
            'category': 'Food',
            'budget_amount': '5000',
            'month': '2026-10'
        }, follow_redirects=True)
        self.assertEqual(res_bud.status_code, 200)

        # Add Savings Goal
        res_sav = self.client.post('/savings/add', data={
            'goal_name': 'Semester Trip',
            'target_amount': '10000',
            'saved_amount': '4000'
        }, follow_redirects=True)
        self.assertEqual(res_sav.status_code, 200)

        # Verify Chart Data API
        res_chart = self.client.get('/api/chart-data')
        self.assertEqual(res_chart.status_code, 200)
        chart_json = json.loads(res_chart.data)
        self.assertTrue(chart_json['success'])
        self.assertIn('Food', chart_json['category_chart']['labels'])

    def test_04_critical_gemini_429_shielding(self):
        """
        CRITICAL REQUIREMENT: Test Gemini HTTP 429 / RESOURCE_EXHAUSTED handling.
        Application MUST return a sanitized friendly message, provide fallback, and NOT CRASH.
        """
        self.client.post('/signup', data={
            'name': 'AI Tester',
            'email': 'teststudent@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # Seed some data first
        self.client.post('/income/update', data={'income': '25000'})
        self.client.post('/expenses/add', data={
            'amount': '4500',
            'category': 'Food',
            'description': 'Groceries',
            'expense_date': '2026-10-01'
        })

        # Call AI endpoint simulating 429
        res = self.client.post('/recommendations/generate?simulate_429=true', follow_redirects=True)
        self.assertEqual(res.status_code, 200) # Returns 200 because fallback is cleanly provided
        res_data = json.loads(res.data)

        self.assertFalse(res_data['success'])
        self.assertEqual(res_data['status_code'], 429)
        self.assertEqual(res_data['error_type'], 'rate_limit')
        
        # Verify NO technical stack trace or Trajectory ID leaked
        self.assertNotIn('Trajectory ID', res_data['message'])
        self.assertNotIn('TraceID', res_data['message'])
        self.assertNotIn('RESOURCE_EXHAUSTED', res_data['message'])
        self.assertIn('temporarily unavailable', res_data['message'])
        
        # Verify fallback data exists
        self.assertTrue(res_data['fallback_available'])
        self.assertIn('Basic spending summary', res_data['fallback_data']['title'])

    def test_05_income_persistence_and_dashboard_display(self):
        """
        Test Income update persistence and Dashboard card rendering.
        Ensures monthly_income updates DB and displays accurately on dashboard.
        """
        # Sign up
        self.client.post('/signup', data={
            'name': 'Income Tester',
            'email': 'teststudent@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # Update Income to ₹35,000
        res_update = self.client.post('/income/update', data={'income': '35000'}, follow_redirects=True)
        self.assertEqual(res_update.status_code, 200)

        # Assert income amount displays in dashboard response
        self.assertIn(b"35000", res_update.data)

        # Query database to verify persistence
        user = query_db("SELECT monthly_income FROM users WHERE email = %s", ("teststudent@example.com",), one=True)
        self.assertIsNotNone(user)
        self.assertEqual(float(user["monthly_income"]), 35000.0)

if __name__ == '__main__':
    unittest.main()
