"""Tests for validators module"""
from backend.utils.validators import Validators


class TestValidators:
    """Test validator functions"""
    
    def test_validate_hostname_valid_domain(self):
        """Test valid domain hostname"""
        assert Validators.validate_hostname("example.com") is True
        assert Validators.validate_hostname("server.example.co.uk") is True
        assert Validators.validate_hostname("my-server.local") is True
    
    def test_validate_hostname_valid_ip(self):
        """Test valid IP address"""
        assert Validators.validate_hostname("192.168.1.1") is True
        assert Validators.validate_hostname("10.0.0.1") is True
        assert Validators.validate_hostname("8.8.8.8") is True
    
    def test_validate_hostname_invalid(self):
        """Test invalid hostname"""
        assert Validators.validate_hostname("") is False
        assert Validators.validate_hostname("invalid..domain") is False
        assert Validators.validate_hostname("999.999.999.999") is False
        assert Validators.validate_hostname("x" * 300) is False
    
    def test_validate_port_valid(self):
        """Test valid port numbers"""
        assert Validators.validate_port(22) is True
        assert Validators.validate_port(80) is True
        assert Validators.validate_port(443) is True
        assert Validators.validate_port(65535) is True
    
    def test_validate_port_invalid(self):
        """Test invalid port numbers"""
        assert Validators.validate_port(0) is False
        assert Validators.validate_port(-1) is False
        assert Validators.validate_port(65536) is False
        assert Validators.validate_port(99999) is False
    
    def test_validate_threshold_valid(self):
        """Test valid threshold values"""
        assert Validators.validate_threshold(0) is True
        assert Validators.validate_threshold(50) is True
        assert Validators.validate_threshold(100) is True
        assert Validators.validate_threshold(85.5) is True
    
    def test_validate_threshold_invalid(self):
        """Test invalid threshold values"""
        assert Validators.validate_threshold(-1) is False
        assert Validators.validate_threshold(101) is False
        assert Validators.validate_threshold(-100) is False
    
    def test_validate_username(self):
        """Test username validation"""
        assert Validators.validate_username("admin") is True
        assert Validators.validate_username("root_user") is True
        assert Validators.validate_username("user-123") is True
        assert Validators.validate_username("u") is False  # Too short
        assert Validators.validate_username("x" * 50) is False  # Too long
    
    def test_validate_email(self):
        """Test email validation"""
        assert Validators.validate_email("test@example.com") is True
        assert Validators.validate_email("user.name@domain.co.uk") is True
        assert Validators.validate_email("invalid@") is False
        assert Validators.validate_email("@example.com") is False
        assert Validators.validate_email("plainaddress") is False
    
    def test_is_sql_injection_attempt(self):
        """Test SQL injection detection"""
        assert Validators.is_sql_injection_attempt("DROP TABLE users") is True
        assert Validators.is_sql_injection_attempt("'; DELETE FROM --") is True
        assert Validators.is_sql_injection_attempt("UNION SELECT * FROM") is True
        assert Validators.is_sql_injection_attempt("normal string") is False
        assert Validators.is_sql_injection_attempt("server1") is False
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        assert Validators.sanitize_string("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        assert Validators.sanitize_string("&lt;test&gt;") == "&amp;lt;test&amp;gt;"
        assert Validators.sanitize_string("normal string") == "normal string"
        
        # Test max length
        long_string = "x" * 2000
        result = Validators.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_validate_and_sanitize_name(self):
        """Test name validation and sanitization"""
        valid, name = Validators.validate_and_sanitize_name("My Server")
        assert valid is True
        assert len(name) > 0
        
        invalid, _ = Validators.validate_and_sanitize_name("DROP TABLE servers")
        assert invalid is False
        
        invalid, _ = Validators.validate_and_sanitize_name("")
        assert invalid is False
    
    def test_validate_file_path(self):
        """Test file path validation"""
        assert Validators.validate_file_path("/home/user/.ssh/id_rsa") is True
        assert Validators.validate_file_path("/etc/ssh/ssh_config") is True
        assert Validators.validate_file_path("../../../etc/passwd") is False  # Path traversal
        assert Validators.validate_file_path("~/.ssh/key") is False  # Tilde not allowed
        assert Validators.validate_file_path("/path/../../secret") is False
    
    def test_validate_alert_threshold(self):
        """Test alert threshold validation"""
        # CPU threshold
        assert Validators.validate_alert_threshold(85.5, "CPU") is True
        assert Validators.validate_alert_threshold(101, "CPU") is False
        
        # Memory threshold
        assert Validators.validate_alert_threshold(90, "MEMORY") is True
        
        # Network threshold (can be higher)
        assert Validators.validate_alert_threshold(5_000_000_000, "NETWORK") is True
        assert Validators.validate_alert_threshold(11_000_000_000, "NETWORK") is False
