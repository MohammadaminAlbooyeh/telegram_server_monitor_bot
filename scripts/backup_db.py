#!/usr/bin/env python3
"""
Database backup utility for PostgreSQL

Creates timestamped backups and manages retention policy.
Usage: python scripts/backup_db.py [--retention-days 30] [--output-dir ./backups]
"""

import os
import sys
import gzip
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class DatabaseBackup:
    """Manage PostgreSQL database backups"""
    
    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_user: str = "monitoring_user",
        db_password: Optional[str] = None,
        db_name: str = "monitoring_bot",
        output_dir: str = "./backups",
        retention_days: int = 30
    ):
        """
        Initialize backup manager
        
        Args:
            db_host: Database host
            db_port: Database port
            db_user: Database user
            db_password: Database password (from environment if None)
            db_name: Database name
            output_dir: Output directory for backups
            retention_days: Retention period for backups
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password or os.getenv("PGPASSWORD", "secure_password")
        self.db_name = db_name
        self.output_dir = Path(output_dir)
        self.retention_days = retention_days
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def backup(self) -> bool:
        """
        Create database backup
        
        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.output_dir / f"backup_{self.db_name}_{timestamp}.sql.gz"
        
        logger.info("Starting database backup to %s", backup_file)
        
        try:
            # Run pg_dump
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            dump_cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-F", "plain",
                self.db_name
            ]
            
            logger.info("Running pg_dump command")
            
            with open(backup_file, "wb") as f:
                # Pipe pg_dump output through gzip
                process = subprocess.Popen(
                    dump_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
                
                with gzip.GzipFile(fileobj=f, mode="wb") as gz:
                    for chunk in iter(lambda: process.stdout.read(8192), b""):
                        gz.write(chunk)
                
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    logger.error("pg_dump failed: %s", stderr.decode())
                    backup_file.unlink()
                    return False
            
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            logger.info("Backup completed successfully: %s (%.2f MB)", backup_file.name, size_mb)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            return True
            
        except FileNotFoundError:
            logger.error("pg_dump not found. Please install PostgreSQL client tools.")
            return False
        except Exception as e:
            logger.error("Backup failed: %s", str(e))
            if backup_file.exists():
                backup_file.unlink()
            return False
    
    def restore(self, backup_file: str) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            logger.error("Backup file not found: %s", backup_file)
            return False
        
        logger.warning("Starting database restore from %s", backup_file)
        logger.warning("WARNING: This will overwrite the existing database!")
        
        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            # Decompress and restore
            logger.info("Decompressing and restoring database")
            
            with gzip.open(backup_path, "rb") as gz:
                process = subprocess.Popen(
                    [
                        "psql",
                        "-h", self.db_host,
                        "-p", str(self.db_port),
                        "-U", self.db_user,
                        "-d", self.db_name
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
                
                _, stderr = process.communicate(gz.read())
                
                if process.returncode != 0:
                    logger.error("Restore failed: %s", stderr.decode())
                    return False
            
            logger.info("Restore completed successfully")
            return True
            
        except FileNotFoundError:
            logger.error("psql not found. Please install PostgreSQL client tools.")
            return False
        except Exception as e:
            logger.error("Restore failed: %s", str(e))
            return False
    
    def list_backups(self) -> list:
        """
        List available backups
        
        Returns:
            List of backup files sorted by date (newest first)
        """
        backups = sorted(
            self.output_dir.glob(f"backup_{self.db_name}_*.sql.gz"),
            reverse=True
        )
        
        logger.info("Found %d backups:", len(backups))
        for backup in backups:
            size_mb = backup.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            logger.info("  - %s (%.2f MB) - %s", backup.name, size_mb, mtime)
        
        return backups
    
    def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup in self.output_dir.glob(f"backup_{self.db_name}_*.sql.gz"):
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            
            if mtime < cutoff_date:
                logger.info("Removing old backup: %s", backup.name)
                backup.unlink()


def main():
    """CLI interface for backup utility"""
    parser = argparse.ArgumentParser(
        description="PostgreSQL database backup utility"
    )
    
    parser.add_argument(
        "action",
        choices=["backup", "restore", "list"],
        help="Backup action to perform"
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Database host (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5432,
        help="Database port (default: 5432)"
    )
    
    parser.add_argument(
        "--user",
        default="monitoring_user",
        help="Database user (default: monitoring_user)"
    )
    
    parser.add_argument(
        "--db",
        default="monitoring_bot",
        help="Database name (default: monitoring_bot)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="./backups",
        help="Output directory for backups (default: ./backups)"
    )
    
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Retention period in days (default: 30)"
    )
    
    parser.add_argument(
        "--file",
        help="Backup file to restore (for restore action)"
    )
    
    args = parser.parse_args()
    
    backup = DatabaseBackup(
        db_host=args.host,
        db_port=args.port,
        db_user=args.user,
        db_name=args.db,
        output_dir=args.output_dir,
        retention_days=args.retention_days
    )
    
    if args.action == "backup":
        success = backup.backup()
        sys.exit(0 if success else 1)
    
    elif args.action == "restore":
        if not args.file:
            logger.error("--file required for restore action")
            sys.exit(1)
        success = backup.restore(args.file)
        sys.exit(0 if success else 1)
    
    elif args.action == "list":
        backups = backup.list_backups()
        sys.exit(0)


if __name__ == "__main__":
    main()
