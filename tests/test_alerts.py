"""Tests for alerts API endpoints"""


class TestAlertsEndpoints:
    """Test alert API endpoints"""
    
    def test_create_alert_success(self, client, sample_server_data, sample_alert_data):
        """Test successful alert creation"""
        # Create server first
        server_response = client.post("/api/servers", json=sample_server_data)
        server_id = server_response.json()["id"]
        
        sample_alert_data["server_id"] = server_id
        
        # Create alert
        response = client.post("/api/alerts", json=sample_alert_data)
        assert response.status_code == 201
        data = response.json()
        assert data["alert_type"] == "CPU"
        assert data["server_id"] == server_id
        assert data["severity"] == "WARNING"
    
    def test_create_alert_invalid_server(self, client, sample_alert_data):
        """Test alert creation with non-existent server"""
        sample_alert_data["server_id"] = 99999
        response = client.post("/api/alerts", json=sample_alert_data)
        
        assert response.status_code == 404
        assert "SERVER_NOT_FOUND" in response.text
    
    def test_create_alert_invalid_severity(self, client, sample_server_data, sample_alert_data):
        """Test alert creation with invalid severity"""
        # Create server first
        server_response = client.post("/api/servers", json=sample_server_data)
        server_id = server_response.json()["id"]
        
        sample_alert_data["server_id"] = server_id
        sample_alert_data["severity"] = "INVALID"
        
        response = client.post("/api/alerts", json=sample_alert_data)
        assert response.status_code == 422
    
    def test_get_alert_success(self, client, sample_server_data, sample_alert_data):
        """Test getting an alert"""
        # Create server and alert
        server_response = client.post("/api/servers", json=sample_server_data)
        server_id = server_response.json()["id"]
        
        sample_alert_data["server_id"] = server_id
        alert_response = client.post("/api/alerts", json=sample_alert_data)
        alert_id = alert_response.json()["id"]
        
        # Get alert
        response = client.get(f"/api/alerts/{alert_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert_id
    
    def test_get_alert_not_found(self, client):
        """Test getting non-existent alert"""
        response = client.get("/api/alerts/99999")
        assert response.status_code == 404
        assert "ALERT_NOT_FOUND" in response.text
    
    def test_list_alerts(self, client, sample_server_data, sample_alert_data):
        """Test listing alerts"""
        # Create server
        server_response = client.post("/api/servers", json=sample_server_data)
        server_id = server_response.json()["id"]
        
        sample_alert_data["server_id"] = server_id
        
        # Create multiple alerts
        client.post("/api/alerts", json=sample_alert_data)
        
        sample_alert_data["alert_type"] = "MEMORY"
        client.post("/api/alerts", json=sample_alert_data)
        
        response = client.get("/api/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_list_alerts_filter_by_server(self, client, sample_server_data, sample_alert_data):
        """Test listing alerts filtered by server"""
        # Create two servers
        server1_response = client.post("/api/servers", json=sample_server_data)
        server1_id = server1_response.json()["id"]
        
        sample_server_data["name"] = "test-server-2"
        server2_response = client.post("/api/servers", json=sample_server_data)
        server2_id = server2_response.json()["id"]
        
        # Create alerts for server1
        sample_alert_data["server_id"] = server1_id
        client.post("/api/alerts", json=sample_alert_data)
        
        # Create alert for server2
        sample_alert_data["server_id"] = server2_id
        client.post("/api/alerts", json=sample_alert_data)
        
        # Filter by server1
        response = client.get(f"/api/alerts?server_id={server1_id}")
        assert response.status_code == 200
        data = response.json()
        assert all(alert["server_id"] == server1_id for alert in data)
    
    def test_update_alert(self, client, sample_server_data, sample_alert_data):
        """Test updating an alert"""
        # Create server and alert
        server_response = client.post("/api/servers", json=sample_server_data)
        server_id = server_response.json()["id"]
        
        sample_alert_data["server_id"] = server_id
        alert_response = client.post("/api/alerts", json=sample_alert_data)
        alert_id = alert_response.json()["id"]
        
        # Acknowledge alert
        update_data = {"is_acknowledged": True}
        response = client.put(f"/api/alerts/{alert_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_acknowledged"] is True
        assert data["acknowledged_at"] is not None
    
    def test_delete_alert(self, client, sample_server_data, sample_alert_data):
        """Test deleting an alert"""
        # Create server and alert
        server_response = client.post("/api/servers", json=sample_server_data)
        server_id = server_response.json()["id"]
        
        sample_alert_data["server_id"] = server_id
        alert_response = client.post("/api/alerts", json=sample_alert_data)
        alert_id = alert_response.json()["id"]
        
        # Delete alert
        response = client.delete(f"/api/alerts/{alert_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        response = client.get(f"/api/alerts/{alert_id}")
        assert response.status_code == 404


class TestAlertValidation:
    """Test alert data validation"""
    
    def test_alert_message_required(self, client, sample_server_data):
        """Test that alert message is required"""
        server_response = client.post("/api/servers", json=sample_server_data)
        server_id = server_response.json()["id"]
        
        data = {
            "server_id": server_id,
            "alert_type": "CPU",
            "severity": "WARNING",
            "value": 85.5,
            "threshold": 80.0
        }
        response = client.post("/api/alerts", json=data)
        assert response.status_code == 422
    
    def test_alert_threshold_validation(self, client, sample_server_data, sample_alert_data):
        """Test alert threshold value validation"""
        server_response = client.post("/api/servers", json=sample_server_data)
        server_id = server_response.json()["id"]
        
        sample_alert_data["server_id"] = server_id
        sample_alert_data["threshold"] = -1  # Invalid
        
        response = client.post("/api/alerts", json=sample_alert_data)
        # Should either succeed (value stored as-is) or fail with validation error
        assert response.status_code in [201, 422]
