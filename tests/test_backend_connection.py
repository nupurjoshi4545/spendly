import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app
from database.db import get_db, init_db, seed_db
from database.queries import (
    get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown
)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
            seed_db()
            yield client


class TestGetUserById:
    def test_get_user_by_id_valid(self, client):
        with app.app_context():
            user = get_user_by_id(1)
            assert user is not None
            assert user['name'] == 'Demo User'
            assert user['email'] == 'demo@spendly.com'
            assert user['member_since'] == 'April 2026'

    def test_get_user_by_id_nonexistent(self, client):
        with app.app_context():
            user = get_user_by_id(9999)
            assert user is None


class TestGetSummaryStats:
    def test_get_summary_stats_with_expenses(self, client):
        with app.app_context():
            stats = get_summary_stats(1)
            assert stats is not None
            assert stats['total_spent'] == 346.24
            assert stats['transaction_count'] == 8
            assert stats['top_category'] == 'Bills'

    def test_get_summary_stats_no_expenses(self, client):
        with app.app_context():
            stats = get_summary_stats(9999)
            assert stats is not None
            assert stats['total_spent'] == 0.0
            assert stats['transaction_count'] == 0
            assert stats['top_category'] == '—'


class TestGetRecentTransactions:
    def test_get_recent_transactions_with_expenses(self, client):
        with app.app_context():
            transactions = get_recent_transactions(1)
            assert len(transactions) == 8
            assert all(key in transactions[0] for key in ['date', 'description', 'category', 'amount'])
            # Check ordered newest-first
            assert transactions[0]['date'] == '2026-04-20'
            assert transactions[-1]['date'] == '2026-04-01'

    def test_get_recent_transactions_no_expenses(self, client):
        with app.app_context():
            transactions = get_recent_transactions(9999)
            assert transactions == []

    def test_get_recent_transactions_limit(self, client):
        with app.app_context():
            transactions = get_recent_transactions(1, limit=3)
            assert len(transactions) == 3


class TestGetCategoryBreakdown:
    def test_get_category_breakdown_with_expenses(self, client):
        with app.app_context():
            breakdown = get_category_breakdown(1)
            assert len(breakdown) == 7
            assert all(key in item for item in breakdown for key in ['name', 'amount', 'pct'])

            # Verify ordered by amount descending
            amounts = [item['amount'] for item in breakdown]
            assert amounts == sorted(amounts, reverse=True)

            # Verify percentages sum to 100
            pct_sum = sum(item['pct'] for item in breakdown)
            assert pct_sum == 100

            # Verify all pct are integers
            assert all(isinstance(item['pct'], int) for item in breakdown)

    def test_get_category_breakdown_no_expenses(self, client):
        with app.app_context():
            breakdown = get_category_breakdown(9999)
            assert breakdown == []


class TestProfileRoute:
    def test_profile_unauthenticated(self, client):
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_profile_authenticated_seed_user(self, client):
        client.post('/login', data={
            'email': 'demo@spendly.com',
            'password': 'demo123'
        })
        response = client.get('/profile')
        assert response.status_code == 200

        data = response.get_data(as_text=True)
        assert 'Demo User' in data
        assert 'demo@spendly.com' in data
        assert '₹' in data
        assert '₹346.24' in data
        assert '8' in data
        assert 'Bills' in data

    def test_profile_new_user_no_expenses(self, client):
        # Register a new user
        client.post('/register', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        # Login as new user
        client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        response = client.get('/profile')
        assert response.status_code == 200

        data = response.get_data(as_text=True)
        assert 'Test User' in data
        assert 'test@example.com' in data
        assert '₹0.00' in data
        assert 'No errors' not in data  # Just ensure it loads without errors
