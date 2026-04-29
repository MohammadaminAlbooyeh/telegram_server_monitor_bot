from database.connection import SessionLocal
from backend.models.server import Server
from datetime import datetime

def seed_data():
    db = SessionLocal()
    
    # Create sample server
    server = Server(
        name="Test Server",
        hostname="localhost",
        ssh_port=22,
        username="root",
        password="password",
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(server)
    db.commit()
    print("Sample data seeded successfully")

if __name__ == "__main__":
    seed_data()