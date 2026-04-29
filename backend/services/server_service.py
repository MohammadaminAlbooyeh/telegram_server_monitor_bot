from sqlalchemy.orm import Session
import logging

from backend.models.server import Server
from backend.schemas.server import ServerCreate, ServerUpdate

logger = logging.getLogger("backend")

class ServerService:
    
    @staticmethod
    def create_server(db: Session, server: ServerCreate) -> Server:
        """Create new server"""
        db_server = Server(**server.dict())
        db.add(db_server)
        db.commit()
        db.refresh(db_server)
        return db_server
    
    @staticmethod
    def get_server(db: Session, server_id: int) -> Server:
        """Get server by ID"""
        return db.query(Server).filter(Server.id == server_id).first()
    
    @staticmethod
    def list_servers(db: Session, skip: int = 0, limit: int = 100) -> list:
        """List all servers"""
        return db.query(Server).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_server(db: Session, server_id: int, server_update: ServerUpdate) -> Server:
        """Update server"""
        server = db.query(Server).filter(Server.id == server_id).first()
        if server:
            update_data = server_update.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(server, key, value)
            db.commit()
            db.refresh(server)
        return server
    
    @staticmethod
    def delete_server(db: Session, server_id: int) -> bool:
        """Delete server"""
        server = db.query(Server).filter(Server.id == server_id).first()
        if server:
            db.delete(server)
            db.commit()
            return True
        return False