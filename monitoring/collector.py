import paramiko
import logging
from typing import Optional, Dict
from config.settings import SSH_TIMEOUT

logger = logging.getLogger("monitoring")

class SSHHandler:
    """Handle SSH connections"""
    
    def __init__(self, hostname: str, port: int, username: str, password: str = None, key_path: str = None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self.client = None
    
    def connect(self) -> bool:
        """Establish SSH connection"""
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
            
            logger.info(f"SSH connection established to {self.hostname}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to {self.hostname}: {str(e)}")
            return False
    
    def execute_command(self, command: str) -> Optional[str]:
        """Execute command on remote server"""
        try:
            if not self.client:
                return None
            
            stdin, stdout, stderr = self.client.exec_command(command, timeout=SSH_TIMEOUT)
            output = stdout.read().decode('utf-8')
            return output
        
        except Exception as e:
            logger.error(f"Failed to execute command on {self.hostname}: {str(e)}")
            return None
    
    def disconnect(self):
        """Close SSH connection"""
        try:
            if self.client:
                self.client.close()
                logger.info(f"SSH connection closed for {self.hostname}")
        except Exception as e:
            logger.error(f"Error closing SSH connection: {str(e)}")


class MetricsCollector:
    """Collect system metrics from servers"""
    
    def __init__(self, server_data: Dict):
        self.server_data = server_data
        self.ssh_handler = SSHHandler(
            hostname=server_data.get('hostname'),
            port=server_data.get('ssh_port', 22),
            username=server_data.get('username'),
            password=server_data.get('password'),
            key_path=server_data.get('ssh_key_path')
        )
    
    def collect_all_metrics(self) -> Optional[Dict]:
        """Collect all metrics from server"""
        try:
            if not self.ssh_handler.connect():
                return None
            
            metrics = {
                'cpu_usage': self.get_cpu_usage(),
                'memory_usage': self.get_memory_usage(),
                'memory_available': self.get_memory_available(),
                'disk_usage': self.get_disk_usage(),
                'disk_available': self.get_disk_available(),
                'network_in': self.get_network_in(),
                'network_out': self.get_network_out(),
                'load_average_1': self.get_load_average()[0] if self.get_load_average() else 0,
                'load_average_5': self.get_load_average()[1] if self.get_load_average() else 0,
                'load_average_15': self.get_load_average()[2] if self.get_load_average() else 0,
                'temperature': self.get_temperature(),
            }
            
            self.ssh_handler.disconnect()
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
            self.ssh_handler.disconnect()
            return None
    
    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            output = self.ssh_handler.execute_command(
                "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'"
            )
            if output:
                return float(output.strip())
        except Exception as e:
            logger.warning(f"Failed to get CPU usage: {str(e)}")
        return 0.0
    
    def get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        try:
            output = self.ssh_handler.execute_command(
                "free | grep Mem | awk '{print ($3/$2) * 100}'"
            )
            if output:
                return float(output.strip())
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {str(e)}")
        return 0.0
    
    def get_memory_available(self) -> float:
        """Get available memory in GB"""
        try:
            output = self.ssh_handler.execute_command(
                "free -g | grep Mem | awk '{print $7}'"
            )
            if output:
                return float(output.strip())
        except Exception as e:
            logger.warning(f"Failed to get available memory: {str(e)}")
        return 0.0
    
    def get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            output = self.ssh_handler.execute_command(
                "df / | tail -1 | awk '{print $5}' | sed 's/%//'"
            )
            if output:
                return float(output.strip())
        except Exception as e:
            logger.warning(f"Failed to get disk usage: {str(e)}")
        return 0.0
    
    def get_disk_available(self) -> float:
        """Get available disk space in GB"""
        try:
            output = self.ssh_handler.execute_command(
                "df / | tail -1 | awk '{print $4/1024/1024}'"
            )
            if output:
                return float(output.strip())
        except Exception as e:
            logger.warning(f"Failed to get available disk: {str(e)}")
        return 0.0
    
    def get_network_in(self) -> float:
        """Get network input bytes"""
        try:
            output = self.ssh_handler.execute_command(
                "cat /proc/net/dev | tail -1 | awk '{print $2}'"
            )
            if output:
                return float(output.strip())
        except Exception as e:
            logger.warning(f"Failed to get network in: {str(e)}")
        return 0.0
    
    def get_network_out(self) -> float:
        """Get network output bytes"""
        try:
            output = self.ssh_handler.execute_command(
                "cat /proc/net/dev | tail -1 | awk '{print $10}'"
            )
            if output:
                return float(output.strip())
        except Exception as e:
            logger.warning(f"Failed to get network out: {str(e)}")
        return 0.0
    
    def get_load_average(self) -> Optional[tuple]:
        """Get load average (1, 5, 15 minutes)"""
        try:
            output = self.ssh_handler.execute_command(
                "cat /proc/loadavg | awk '{print $1, $2, $3}'"
            )
            if output:
                values = output.strip().split()
                return tuple(float(v) for v in values)
        except Exception as e:
            logger.warning(f"Failed to get load average: {str(e)}")
        return None
    
    def get_temperature(self) -> Optional[float]:
        """Get CPU temperature if available"""
        try:
            output = self.ssh_handler.execute_command(
                "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000}'"
            )
            if output and output.strip():
                return float(output.strip())
        except Exception as e:
            logger.warning(f"Failed to get temperature: {str(e)}")
        return None