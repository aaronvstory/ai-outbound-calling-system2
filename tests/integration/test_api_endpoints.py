"""
Integration tests for API endpoints
"""
import pytest
import json

class TestCallEndpoints:
    def test_create_call_success(self, client):
        """Test successful call creation"""
        data = {
            'caller_name': 'John Doe',
            'caller_phone': '+1234567890',
            'phone_number': '+0987654321',
            'account_action': 'Test account adjustment',
            'additional_info': 'Test info'
        }
        
        response = client.post('/api/calls', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'call_id' in result
    
    def test_create_call_validation_error(self, client):
        """Test call creation with validation errors"""
        data = {
            'caller_name': '',  # Empty name
            'caller_phone': 'invalid',  # Invalid phone
            'phone_number': '+0987654321',
            'account_action': 'Test action'
        }
        
        response = client.post('/api/calls',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'details' in result
    
    def test_get_calls(self, client):
        """Test getting calls list"""
        response = client.get('/api/calls')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'calls' in result
        assert isinstance(result['calls'], list)
    
    def test_get_calls_with_pagination(self, client):
        """Test getting calls with pagination"""
        response = client.get('/api/calls?page=1&per_page=10')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert result['page'] == 1
        assert result['per_page'] == 10
    
    def test_get_call_not_found(self, client):
        """Test getting non-existent call"""
        response = client.get('/api/calls/nonexistent-id')
        
        assert response.status_code == 404
        result = response.get_json()
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

class TestConfigEndpoints:
    def test_get_config(self, client):
        """Test getting system configuration"""
        response = client.get('/api/config')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'config' in result
        assert 'version' in result['config']
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['status'] == 'healthy'
        assert 'version' in result

class TestAnalyticsEndpoints:
    def test_get_analytics_metrics(self, client):
        """Test getting analytics metrics"""
        response = client.get('/api/analytics/metrics')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'metrics' in result
    
    def test_get_analytics_metrics_with_days(self, client):
        """Test getting analytics metrics with days parameter"""
        response = client.get('/api/analytics/metrics?days=7')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True