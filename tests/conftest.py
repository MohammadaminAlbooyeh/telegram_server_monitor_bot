"""Pytest configuration and fixtures"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

from backend.models.database import Base, get_db
from backend.main import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client"""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture(scope="function")
def sample_server_data():
    """Sample server data for tests"""
    return {
        "name": "test-server-1",
        "hostname": "192.168.1.100",
        "ssh_port": 22,
        "username": "testuser",
        "password": "testpass123",
        "description": "Test server for monitoring",
        "is_active": True
    }


@pytest.fixture(scope="function")
def sample_alert_data():
    """Sample alert data for tests"""
    return {
        "server_id": 1,
        "alert_type": "CPU",
        "severity": "WARNING",
        "message": "CPU usage exceeded threshold",
        "value": 85.5,
        "threshold": 80.0
    }


@pytest.fixture(scope="function")
def sample_metric_data():
    """Sample metric data for tests"""
    return {
        "server_id": 1,
        "cpu_usage": 45.5,
        "memory_usage": 62.3,
        "memory_available": 8192.0,
        "disk_usage": 75.2,
        "disk_available": 256000.0,
        "network_in": 1024000.0,
        "network_out": 512000.0,
        "load_average_1": 1.5,
        "load_average_5": 1.2,
        "load_average_15": 1.0,
        "temperature": 65.5
    }
