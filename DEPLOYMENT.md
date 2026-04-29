# Deployment Guide

Comprehensive guide for deploying the Telegram Server Monitor Bot to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [SSL/HTTPS Configuration](#sslhttps-configuration)
5. [Database Setup](#database-setup)
6. [Backup Strategy](#backup-strategy)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker & Docker Compose 1.29+
- PostgreSQL 15+ (if not using Docker)
- Python 3.11+
- Telegram Bot API token
- Valid domain name (for SSL certificates)

## Environment Setup

### 1. Create Environment Files

```bash
# Development (local testing)
cat .env.development

# Staging (pre-production)
cp .env.staging .env.staging && nano .env.staging

# Production (live deployment)
cp .env.production .env.production && nano .env.production
```

**Critical Settings for Production:**
- `SECRET_KEY`: Use strong 32-character random key
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- `TELEGRAM_BOT_TOKEN`: Get from @BotFather on Telegram
- `DATABASE_URL`: PostgreSQL connection string
- `BACKEND_URL`: Your domain (https://yourdomain.com)
- `ALLOWED_USERS`: Telegram user IDs authorized to use bot

### 2. SSL Certificates

**Using Let's Encrypt (Recommended):**

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d yourdomain.com

# Copy to certs directory
mkdir -p certs
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem certs/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem certs/key.pem
sudo chown $USER:$USER certs/*
chmod 600 certs/key.pem
```

**Self-Signed Certificate (Testing):**

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -nodes \
  -out certs/cert.pem -keyout certs/key.pem -days 365
```

## Docker Deployment

### 1. Development Environment

```bash
# Set environment
export APP_ENV=development

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### 2. Staging/Production

```bash
# Use production-specific compose file
docker-compose -f docker-compose.prod.yml up -d

# Verify services
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. Database Initialization

```bash
# Connect to container
docker-compose exec backend bash

# Initialize database
python scripts/setup_db.py

# Seed test data (optional)
python database/seed_data.py
```

## SSL/HTTPS Configuration

### Nginx Reverse Proxy

The production setup includes Nginx for:
- SSL/TLS termination
- Rate limiting
- Request logging
- Security headers

**Verify SSL Configuration:**

```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443

# Check certificate expiry
openssl x509 -enddate -noout -in certs/cert.pem

# Test with curl
curl -v https://yourdomain.com/api/health
```

### Certificate Renewal

**For Let's Encrypt with auto-renewal:**

```bash
# Auto-renewal via cron (runs at 2 AM daily)
sudo crontab -e
# Add: 0 2 * * * certbot renew --quiet && docker restart monitoring_nginx
```

## Database Setup

### 1. PostgreSQL Configuration

**Connection Settings:**
- Host: `postgres` (Docker) or `localhost` (local)
- Port: `5432`
- User: `monitoring_user`
- Database: `monitoring_bot`

**Verify Connection:**

```bash
docker-compose exec postgres psql -U monitoring_user -d monitoring_bot -c "SELECT version();"
```

### 2. Database Backup

**Manual Backup:**

```bash
python scripts/backup_db.py backup \
  --host localhost \
  --user monitoring_user \
  --db monitoring_bot
```

**Automated Backup (Cron):**

```bash
# Daily 2 AM backup with 30-day retention
0 2 * * * cd /app && python scripts/backup_db.py backup --retention-days 30 >> /var/log/backup.log 2>&1
```

**Restore from Backup:**

```bash
python scripts/backup_db.py restore \
  --file backups/backup_monitoring_bot_20240101_000000.sql.gz
```

### 3. Database Indexes

Indexes are automatically created on startup:

```bash
# Verify indexes
docker-compose exec postgres psql -U monitoring_user -d monitoring_bot -c "\d metrics"
```

## Monitoring & Logging

### Health Check Endpoints

```bash
# Basic health
curl https://yourdomain.com/api/health

# Detailed metrics
curl https://yourdomain.com/api/health/detailed

# Kubernetes readiness
curl https://yourdomain.com/api/health/ready

# Kubernetes liveness
curl https://yourdomain.com/api/health/live

# Scheduler status
curl https://yourdomain.com/api/health/scheduler
```

### View Logs

```bash
# Backend logs
docker-compose logs -f backend

# Telegram bot logs
docker-compose logs -f bot

# Database logs
docker-compose logs -f postgres

# Nginx access logs
docker-compose logs -f nginx

# All logs with timestamps
docker-compose logs -f --timestamps
```

### Log Rotation

Logs are automatically rotated with docker-compose.yml configuration:
- Max file size: 10MB
- Max files: 3 (30MB total)

## Export Data

### Metrics Export

```bash
# CSV format
curl -H "Authorization: Bearer $TOKEN" \
  "https://yourdomain.com/api/export/metrics/csv?days=7" \
  -o metrics.csv

# JSON format
curl -H "Authorization: Bearer $TOKEN" \
  "https://yourdomain.com/api/export/metrics/json?days=7" \
  -o metrics.json
```

### Alerts Export

```bash
# CSV format with filtering
curl -H "Authorization: Bearer $TOKEN" \
  "https://yourdomain.com/api/export/alerts/csv?days=7&status_filter=resolved" \
  -o alerts.csv

# JSON format
curl -H "Authorization: Bearer $TOKEN" \
  "https://yourdomain.com/api/export/alerts/json?days=7" \
  -o alerts.json
```

## Rate Limiting

Default: 30 requests/minute per IP (configurable via `RATE_LIMIT_REQUESTS_PER_MINUTE`)

**Rate Limit Headers:**
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1234567890
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
docker-compose down
sed -i 's/"8000:8000"/"8001:8000"/' docker-compose.yml
docker-compose up -d
```

### Database Connection Issues

```bash
# Test connection
docker-compose exec backend python -c "from backend.models.database import SessionLocal; db = SessionLocal(); print('Connected')"

# Check PostgreSQL service
docker-compose exec postgres pg_isready
```

### SSL Certificate Errors

```bash
# Check certificate validity
openssl x509 -in certs/cert.pem -text -noout

# Update certificate
sudo certbot renew --force-renewal
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem certs/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem certs/key.pem
```

### Memory Issues

```bash
# Check resource usage
docker stats

# Limit memory (docker-compose.yml)
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
```

## Backup Checklist

- [ ] Daily automated backups configured
- [ ] Backup retention policy set (30-90 days recommended)
- [ ] Test restore procedure
- [ ] Off-site backup storage configured
- [ ] Certificate renewal automated
- [ ] SSL expiry monitoring set up

## Security Best Practices

1. **Update Dependencies**: `pip install --upgrade -r requirements.txt`
2. **Change Default Passwords**: Update `POSTGRES_PASSWORD` in docker-compose
3. **Use Strong Keys**: Generate cryptographically secure `SECRET_KEY`
4. **Restrict Access**: Configure firewall rules and ALLOWED_USERS
5. **Monitor Logs**: Review logs regularly for suspicious activity
6. **Enable HTTPS Only**: Configure `CORS_ORIGINS` with https:// URLs
7. **Rate Limiting**: Adjust based on usage patterns

## Performance Tuning

### Database

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### Application

- Enable caching for frequently accessed data
- Adjust `METRICS_COLLECTION_INTERVAL` (default: 300s)
- Tune connection pool: `pool_size` and `max_overflow` in DATABASE_URL

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review health endpoints: `/api/health/detailed`
3. Consult documentation: [README.md](README.md)
