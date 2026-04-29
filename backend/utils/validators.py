import logging
import re
import html

logger = logging.getLogger("backend")

class Validators:
    """Input validators to prevent injection attacks and validate data"""
    
    # Regex patterns
    HOSTNAME_PATTERN = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    IP_PATTERN = r'^((25[0-5]|(2[0-4]|1\d)?[0-9])\.?\b){4}$'
    USERNAME_PATTERN = r'^[a-zA-Z0-9_\-\.]{3,32}$'
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%\-+]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    PATH_PATTERN = r'^[a-zA-Z0-9/_\.\-~]+$'  # Safe file path pattern
    
    # SQL injection patterns
    SQL_KEYWORDS = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT', 'UNION', 'ALTER', 'EXEC', 'EXECUTE', '--', '/*', '*/']
    
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """Validate hostname - must be valid domain or IP"""
        if not hostname or len(hostname) > 255:
            return False
        
        # Check if it's a valid domain or IP
        is_valid_domain = re.match(Validators.HOSTNAME_PATTERN, hostname) is not None
        is_valid_ip = re.match(Validators.IP_PATTERN, hostname) is not None
        
        return is_valid_domain or is_valid_ip
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """Validate port number"""
        return isinstance(port, int) and 1 <= port <= 65535
    
    @staticmethod
    def validate_threshold(threshold: float) -> bool:
        """Validate threshold percentage"""
        try:
            val = float(threshold)
            return 0 <= val <= 100
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate SSH username"""
        if not username or len(username) > 32:
            return False
        return re.match(Validators.USERNAME_PATTERN, username) is not None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        if not email or len(email) > 254:
            return False
        return re.match(Validators.EMAIL_PATTERN, email) is not None
    
    @staticmethod
    def validate_file_path(path: str) -> bool:
        """Validate file path to prevent path traversal"""
        if not path or len(path) > 4096:
            return False
        
        # Prevent path traversal attacks
        if '..' in path or path.startswith('~'):
            return False
        
        return re.match(Validators.PATH_PATTERN, path) is not None
    
    @staticmethod
    def is_sql_injection_attempt(value: str) -> bool:
        """Detect potential SQL injection attempts"""
        if not isinstance(value, str):
            return False
        
        value_upper = value.upper()
        
        for keyword in Validators.SQL_KEYWORDS:
            if keyword in value_upper:
                return True
        
        # Check for common SQL injection patterns
        if re.search(r"[';\"\\]|--", value):
            return True
        
        return False
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS"""
        if not isinstance(value, str):
            return str(value)[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        # Remove control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        # Limit length
        value = value[:max_length]
        
        return value
    
    @staticmethod
    def validate_and_sanitize_name(name: str, max_length: int = 255) -> tuple[bool, str]:
        """Validate and sanitize name field"""
        if not name or not isinstance(name, str):
            return False, ""
        
        if len(name) > max_length:
            return False, ""
        
        # Check for SQL injection
        if Validators.is_sql_injection_attempt(name):
            return False, ""
        
        sanitized = Validators.sanitize_string(name, max_length)
        
        # Name should have at least 1 character after sanitization
        if not sanitized.strip():
            return False, ""
        
        return True, sanitized
    
    @staticmethod
    def validate_description(description: str, max_length: int = 2000) -> tuple[bool, str]:
        """Validate and sanitize description"""
        if not description or not isinstance(description, str):
            return True, ""  # Description is optional
        
        if len(description) > max_length:
            return False, ""
        
        if Validators.is_sql_injection_attempt(description):
            return False, ""
        
        sanitized = Validators.sanitize_string(description, max_length)
        return True, sanitized
    
    @staticmethod
    def validate_alert_threshold(threshold: float, metric_type: str) -> bool:
        """Validate alert threshold based on metric type"""
        try:
            val = float(threshold)
        except (ValueError, TypeError):
            return False
        
        # CPU, Memory, Disk are percentages (0-100)
        if metric_type in ['CPU', 'MEMORY', 'DISK']:
            return 0 <= val <= 100
        
        # Network can be higher (bytes)
        if metric_type == 'NETWORK':
            return 0 <= val <= 10_000_000_000  # 10GB
        
        return 0 <= val <= 100