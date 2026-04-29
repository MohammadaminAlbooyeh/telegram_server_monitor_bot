from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from backend.models.server import Server
from datetime import datetime

def add_server():
    db = SessionLocal()
    
    name = input("Enter server name: ")
    hostname = input("Enter hostname/IP: ")
    ssh_port = int(input("Enter SSH port (default 22): ") or "22")
    username = input("Enter SSH username: ")
    password = input("Enter SSH password: ")
    
    server = Server(
        name=name,
        hostname=hostname,
        ssh_port=ssh_port,
        username=username,
        password=password,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(server)
    db.commit()
    print(f"Server '{name}' added successfully!")

if __name__ == "__main__":
    add_server()
