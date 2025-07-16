# Quick Start Guide - Face Tracking System Backend

## 🚀 Rapid Setup (5 minutes)

### Option 1: Docker Compose (Recommended)
```bash
# Clone and navigate
git clone <repository>
cd face-tracking-system/backend

# Start everything with Docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Option 2: Local Development
```bash
# Clone and navigate
git clone <repository>
cd face-tracking-system/backend

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your database settings

# Start development server
python start.py --reload
```

## 🎯 Essential Commands

### Development
```bash
# Start with auto-reload
python start.py --reload --log-level debug

# Start on different port
python start.py --port 8001

# Multiple workers for testing
python start.py --workers 2
```

### Docker Management
```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f backend
docker-compose logs -f db

# Restart specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Clean up (removes volumes)
docker-compose down -v
```

### Database Management
```bash
# Connect to database (if using Docker)
docker-compose exec db psql -U postgres -d face_tracking

# Manual database creation (local)
sudo -u postgres createdb face_tracking
sudo -u postgres createuser --interactive
```

## 🔧 Configuration Quick Reference

### Environment Variables (.env)
```bash
# Minimal required configuration
SECRET_KEY=your-secret-key-here
DB_HOST=localhost
DB_NAME=face_tracking
DB_USER=postgres
DB_PASSWORD=your_password

# Optional optimizations
MAX_CONCURRENT_STREAMS=5
FACE_RECOGNITION_TOLERANCE=0.6
LOG_LEVEL=INFO
```

## 📡 API Testing

### Health Check
```bash
curl http://localhost:8000/
```

### Authentication
```bash
# Login (you'll need to create a user first via database)
curl -X POST "http://localhost:8000/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token for protected endpoints
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/auth/secure/
```

### Video Streaming
```bash
# Test camera stream (open in browser)
http://localhost:8000/stream/0

# Check camera status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/stream/status/0
```

## 🛠️ Common Issues & Solutions

### Camera Access Issues
```bash
# Check camera permissions
ls -l /dev/video*
sudo usermod -a -G video $USER

# Test camera in Python
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d face_tracking
```

### Port Already in Use
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or use different port
python start.py --port 8001
```

### Dependencies Issues
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Clear pip cache
pip cache purge

# Update pip
pip install --upgrade pip
```

## 📊 Monitoring

### View Logs
```bash
# Real-time logs
tail -f logs/app.log

# Error logs only
grep "ERROR" logs/app.log

# Docker logs
docker-compose logs -f backend
```

### Health Checks
```bash
# API health
curl http://localhost:8000/

# Database health
docker-compose exec db pg_isready -U postgres

# Container status
docker-compose ps
```

## 🔐 Security Setup

### Create Admin User
```sql
-- Connect to database and run:
INSERT INTO roles (role_name) VALUES ('admin'), ('user');
INSERT INTO users (username, password_hash, role_id, status) 
VALUES ('admin', '$2b$12$...', 1, 'active');
-- Use utils/security.py hash_password() to generate password_hash
```

### Production Security
```bash
# Generate strong secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set production environment
export ENVIRONMENT=production
export DEBUG=false
```

## 🚀 Production Deployment

### Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/face-tracking.service

# Enable and start
sudo systemctl enable face-tracking
sudo systemctl start face-tracking
sudo systemctl status face-tracking
```

### Nginx Proxy
```bash
# Install nginx
sudo apt install nginx

# Configure proxy (see README.md for config)
sudo nano /etc/nginx/sites-available/face-tracking

# Enable site
sudo ln -s /etc/nginx/sites-available/face-tracking /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📞 Get Help

### Documentation
- Full README: `README.md`
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Debugging
```bash
# Verbose logging
python start.py --log-level debug

# Check configuration
python -c "from app.config import settings; print(settings.DATABASE_URL)"

# Test imports
python -c "import cv2, face_recognition, fastapi; print('All good!')"
```

### Useful URLs
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/
- **Video Stream**: http://localhost:8000/stream/0
- **Admin Panel**: http://localhost:8000/docs (use for API testing)

---

**Need more help?** Check the full `README.md` or create an issue in the repository.