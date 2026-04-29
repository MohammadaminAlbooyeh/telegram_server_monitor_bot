"""Tests for servers API endpoints"""


class TestServersEndpoints:
    """Test server API endpoints"""
    
    def test_create_server_success(self, client, sample_server_data):
        """Test successful server creation"""
        response = client.post("/api/servers", json=sample_server_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_server_data["name"]
        assert data["hostname"] == sample_server_data["hostname"]
        assert data["id"] is not None
    
    def test_create_server_duplicate_name(self, client, sample_server_data):
        """Test server creation with duplicate name"""
        # Create first server
        client.post("/api/servers", json=sample_server_data)
        
        # Try to create duplicate
        response = client.post("/api/servers", json=sample_server_data)
        assert response.status_code == 409  # Conflict
        assert "DUPLICATE_RESOURCE" in response.text
    
    def test_create_server_invalid_hostname(self, client, sample_server_data):
        """Test server creation with invalid hostname"""
        sample_server_data["hostname"] = "invalid..hostname"
        response = client.post("/api/servers", json=sample_server_data)
        
        assert response.status_code == 422  # Unprocessable entity
    
    def test_create_server_invalid_port(self, client, sample_server_data):
        """Test server creation with invalid port"""
        sample_server_data["ssh_port"] = 99999
        response = client.post("/api/servers", json=sample_server_data)
        
        assert response.status_code == 422
    
    def test_get_server_success(self, client, sample_server_data):
        """Test getting a server"""
        # Create server first
        create_response = client.post("/api/servers", json=sample_server_data)
        server_id = create_response.json()["id"]
        
        # Get server
        response = client.get(f"/api/servers/{server_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == server_id
        assert data["name"] == sample_server_data["name"]
    
    def test_get_server_not_found(self, client):
        """Test getting non-existent server"""
        response = client.get("/api/servers/99999")
        assert response.status_code == 404
        assert "SERVER_NOT_FOUND" in response.text
    
    def test_list_servers(self, client, sample_server_data):
        """Test listing servers"""
        # Create multiple servers
        client.post("/api/servers", json=sample_server_data)
        
        sample_server_data["name"] = "test-server-2"
        client.post("/api/servers", json=sample_server_data)
        
        response = client.get("/api/servers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_list_servers_with_pagination(self, client, sample_server_data):
        """Test server listing with pagination"""
        # Create 5 servers
        for i in range(5):
            sample_server_data["name"] = f"server-{i}"
            client.post("/api/servers", json=sample_server_data)
        
        # Test limit
        response = client.get("/api/servers?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Test skip
        response = client.get("/api/servers?skip=2&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_update_server(self, client, sample_server_data):
        """Test updating a server"""
        # Create server
        create_response = client.post("/api/servers", json=sample_server_data)
        server_id = create_response.json()["id"]
        
        # Update server
        update_data = {"description": "Updated description"}
        response = client.put(f"/api/servers/{server_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
    
    def test_update_server_duplicate_name(self, client, sample_server_data):
        """Test updating server with duplicate name"""
        # Create two servers
        response1 = client.post("/api/servers", json=sample_server_data)
        server1_id = response1.json()["id"]
        
        sample_server_data["name"] = "test-server-2"
        client.post("/api/servers", json=sample_server_data)
        
        # Try to update server1 with server2's name
        update_data = {"name": "test-server-2"}
        response = client.put(f"/api/servers/{server1_id}", json=update_data)
        
        assert response.status_code == 409  # Conflict
    
    def test_delete_server(self, client, sample_server_data):
        """Test deleting a server"""
        # Create server
        create_response = client.post("/api/servers", json=sample_server_data)
        server_id = create_response.json()["id"]
        
        # Delete server
        response = client.delete(f"/api/servers/{server_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        response = client.get(f"/api/servers/{server_id}")
        assert response.status_code == 404
    
    def test_delete_nonexistent_server(self, client):
        """Test deleting non-existent server"""
        response = client.delete("/api/servers/99999")
        assert response.status_code == 404


class TestServerValidation:
    """Test server data validation"""
    
    def test_server_name_required(self, client):
        """Test that server name is required"""
        data = {
            "hostname": "example.com",
            "ssh_port": 22,
            "username": "admin"
        }
        response = client.post("/api/servers", json=data)
        assert response.status_code == 422
    
    def test_server_hostname_required(self, client, sample_server_data):
        """Test that hostname is required"""
        del sample_server_data["hostname"]
        response = client.post("/api/servers", json=sample_server_data)
        assert response.status_code == 422
    
    def test_server_username_required(self, client, sample_server_data):
        """Test that username is required"""
        del sample_server_data["username"]
        response = client.post("/api/servers", json=sample_server_data)
        assert response.status_code == 422
    
    def test_server_ssh_port_default(self, client, sample_server_data):
        """Test SSH port defaults to 22"""
        del sample_server_data["ssh_port"]
        response = client.post("/api/servers", json=sample_server_data)
        
        assert response.status_code == 201
        assert response.json()["ssh_port"] == 22
