from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from typing import Optional

from backend.models.database import get_db, Server
from backend.schemas.server import ServerCreate, ServerResponse, ServerUpdate
from backend.utils.exceptions import (
    ServerNotFound, DuplicateResource, DatabaseError, to_http_exception
)

logger = logging.getLogger("backend")
router = APIRouter()

@router.get("/servers", response_model=list[ServerResponse])
async def list_servers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all servers with optional filters"""
    try:
        query = db.query(Server)
        
        if is_active is not None:
            query = query.filter(Server.is_active == is_active)
        
        servers = query.offset(skip).limit(limit).all()
        return servers
    
    except Exception as e:
        logger.error(f"Error listing servers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "DATABASE_ERROR", "message": "Failed to retrieve servers"}
        )

@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(server_id: int, db: Session = Depends(get_db)):
    """Get single server by ID"""
    try:
        if server_id <= 0:
            raise HTTPException(
                status_code=422,
                detail={"error": "VALIDATION_ERROR", "message": "Server ID must be positive"}
            )
        
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            raise ServerNotFound(server_id)
        
        return server
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving server {server_id}: {str(e)}")
        raise to_http_exception(DatabaseError(f"Failed to retrieve server: {str(e)}"))

@router.post("/servers", response_model=ServerResponse, status_code=201)
async def create_server(
    server: ServerCreate,
    db: Session = Depends(get_db)
):
    """Create new server with validation"""
    try:
        # Check for duplicate server name
        existing = db.query(Server).filter(Server.name == server.name).first()
        if existing:
            raise DuplicateResource("Server", "name", server.name)
        
        # Verify no duplicate hostname+port combination
        existing_host = db.query(Server).filter(
            Server.hostname == server.hostname,
            Server.ssh_port == server.ssh_port
        ).first()
        if existing_host:
            raise DuplicateResource("Server", "hostname:port", f"{server.hostname}:{server.ssh_port}")
        
        db_server = Server(**server.dict())
        db.add(db_server)
        db.commit()
        db.refresh(db_server)
        
        logger.info(f"Server created successfully: {server.name}")
        return db_server
    
    except (DuplicateResource,) as e:
        db.rollback()
        raise to_http_exception(e)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating server: {str(e)}")
        raise to_http_exception(DatabaseError(f"Failed to create server: {str(e)}"))

@router.put("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    server_update: ServerUpdate,
    db: Session = Depends(get_db)
):
    """Update server with validation"""
    try:
        if server_id <= 0:
            raise HTTPException(
                status_code=422,
                detail={"error": "VALIDATION_ERROR", "message": "Server ID must be positive"}
            )
        
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            raise ServerNotFound(server_id)
        
        update_data = server_update.dict(exclude_unset=True)
        
        # Check for duplicate name if name is being updated
        if 'name' in update_data and update_data['name'] != server.name:
            existing = db.query(Server).filter(
                Server.name == update_data['name'],
                Server.id != server_id
            ).first()
            if existing:
                raise DuplicateResource("Server", "name", update_data['name'])
        
        for key, value in update_data.items():
            setattr(server, key, value)
        
        server.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(server)
        
        logger.info(f"Server updated successfully: {server.name}")
        return server
    
    except (ServerNotFound, DuplicateResource) as e:
        db.rollback()
        raise to_http_exception(e)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating server {server_id}: {str(e)}")
        raise to_http_exception(DatabaseError(f"Failed to update server: {str(e)}"))

@router.delete("/servers/{server_id}", status_code=204)
async def delete_server(server_id: int, db: Session = Depends(get_db)):
    """Delete server"""
    try:
        if server_id <= 0:
            raise HTTPException(
                status_code=422,
                detail={"error": "VALIDATION_ERROR", "message": "Server ID must be positive"}
            )
        
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            raise ServerNotFound(server_id)
        
        server_name = server.name
        db.delete(server)
        db.commit()
        
        logger.info(f"Server deleted successfully: {server_name}")
        return None
    
    except ServerNotFound as e:
        raise to_http_exception(e)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting server {server_id}: {str(e)}")
        raise to_http_exception(DatabaseError(f"Failed to delete server: {str(e)}"))