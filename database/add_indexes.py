"""Add database indexes for performance optimization"""
from sqlalchemy import text
from backend.models.database import SessionLocal, engine

def add_indexes():
    """Create composite indexes for frequently used queries"""
    db = SessionLocal()
    
    try:
        # Index for metric queries by server and timestamp
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_metrics_server_timestamp 
            ON metrics(server_id, timestamp DESC)
        """))
        print("✓ Created index: idx_metrics_server_timestamp")
        
        # Index for alert queries by server and created_at
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_alerts_server_created
            ON alerts(server_id, created_at DESC)
        """))
        print("✓ Created index: idx_alerts_server_created")
        
        # Index for unresolved alerts
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_alerts_unresolved
            ON alerts(is_resolved, created_at DESC)
            WHERE is_resolved = false
        """))
        print("✓ Created index: idx_alerts_unresolved")
        
        # Index for active servers
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_servers_active
            ON servers(is_active, last_check DESC)
            WHERE is_active = true
        """))
        print("✓ Created index: idx_servers_active")
        
        # Index for metric cleanup queries
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_metrics_created
            ON metrics(created_at DESC)
        """))
        print("✓ Created index: idx_metrics_created")
        
        db.commit()
        print("\nAll indexes created successfully!")
    
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    add_indexes()
