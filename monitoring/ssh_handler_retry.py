"""SSH handler with retry logic"""
import paramiko
import logging
import time
from typing import Optional, Dict, Callable
from config.settings import SSH_TIMEOUT, SSH_RETRIES

logger = logging.getLogger("monitoring")


class SSHHandlerWithRetry:
    """SSH handler with exponential backoff retry logic"""
    
    def __init__(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str = None,
        key_path: str = None,
        max_retries: int = SSH_RETRIES,
        base_wait: float = 1.0
    ):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self.client = None
        self.max_retries = max_retries
        self.base_wait = base_wait
    
    def connect_with_retry(self) -> bool:
        """Establish SSH connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if self.key_path:
                    self.client.connect(
                        hostname=self.hostname,
                        port=self.port,
                        username=self.username,
                        key_filename=self.key_path,
                        timeout=SSH_TIMEOUT,
                    )
                else:
                    self.client.connect(
                        hostname=self.hostname,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                        timeout=SSH_TIMEOUT
                    )
                
                logger.info(f"SSH connection established to {self.hostname} (attempt {attempt + 1})")
                return True
            
            except (paramiko.ssh_exception.SSHException, Exception) as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.base_wait * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"SSH connection attempt {attempt + 1}/{self.max_retries} failed to {self.hostname}: {str(e)}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"SSH connection failed after {self.max_retries} attempts to {self.hostname}: {str(e)}"
                    )
                    return False
        
        return False
    
    def execute_command_with_retry(self, command: str) -> Optional[str]:
        """Execute command with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if not self.client:
                    logger.error(f"SSH client not connected to {self.hostname}")
                    return None
                
                stdin, stdout, stderr = self.client.exec_command(command, timeout=SSH_TIMEOUT)
                output = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                
                if error:
                    logger.warning(f"Command error on {self.hostname}: {error}")
                
                return output
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.base_wait * (2 ** attempt)
                    logger.warning(
                        f"Command execution attempt {attempt + 1}/{self.max_retries} failed on {self.hostname}: {str(e)}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    
                    # Try to reconnect
                    if not self.connect_with_retry():
                        return None
                else:
                    logger.error(
                        f"Command execution failed after {self.max_retries} attempts on {self.hostname}: {str(e)}"
                    )
                    return None
        
        return None
    
    def disconnect(self):
        """Close SSH connection"""
        try:
            if self.client:
                self.client.close()
                logger.info(f"SSH connection closed for {self.hostname}")
        except Exception as e:
            logger.error(f"Error closing SSH connection to {self.hostname}: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect_with_retry()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
