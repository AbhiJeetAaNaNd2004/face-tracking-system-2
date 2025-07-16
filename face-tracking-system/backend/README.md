# Face Tracking System - Backend

A professional FastAPI backend for face detection, recognition, and attendance tracking with real-time video streaming capabilities.

## 🚀 Features

- **Real-time Face Detection & Recognition**: Advanced face detection with confidence scoring
- **Video Streaming**: MJPEG streaming with face detection overlay
- **Attendance Tracking**: Automatic attendance recording with employee identification
- **User Management**: JWT-based authentication with role-based access control
- **Employee Management**: Complete CRUD operations for employee data
- **Face Embeddings**: Enroll and manage face embeddings for recognition
- **Background Monitoring**: Continuous camera monitoring for automated attendance
- **Rate Limiting**: Protection against brute force attacks
- **Structured Logging**: Comprehensive logging with rotation and color coding
- **Configuration Management**: Environment-based configuration with validation

## 📋 Requirements

### System Requirements
- Python 3.8+
- PostgreSQL 12+
- Camera(s) for video capture
- Minimum 4GB RAM (8GB recommended)
- OpenCV-compatible camera drivers

### Python Dependencies
See `requirements.txt` for complete list. Key dependencies:
- FastAPI 0.104+
- OpenCV 4.8+
- face-recognition 1.3+
- SQLAlchemy 2.0+
- PostgreSQL driver (psycopg2)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd face-tracking-system/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
# or
brew install postgresql  # macOS

# Create database
sudo -u postgres createdb face_tracking
sudo -u postgres createuser --interactive
```

### 5. Environment Configuration
```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your configuration
nano .env
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=face_tracking
DB_USER=postgres
DB_PASSWORD=your_password

# Security Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application Configuration
ENVIRONMENT=development  # or production
DEBUG=true
LOG_LEVEL=INFO

# Face Recognition Settings
FACE_RECOGNITION_TOLERANCE=0.6
FACE_DETECTION_MODEL=hog
FACE_ENCODING_MODEL=large

# Camera Configuration
DEFAULT_CAMERA_ID=0
MAX_CONCURRENT_STREAMS=5
FRAME_RATE=30
```

### Production Configuration

For production deployment:
1. Set `ENVIRONMENT=production`
2. Set `DEBUG=false`
3. Use a strong `SECRET_KEY`
4. Configure proper database credentials
5. Set up SSL/TLS certificates
6. Configure firewall rules

## 🚦 Running the Application

### Development Mode
```bash
# Using the startup script (recommended)
python start.py --reload --log-level debug

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
# Single worker
python start.py --host 0.0.0.0 --port 8000

# Multiple workers (recommended for production)
python start.py --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn (alternative)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment
```bash
# Build image
docker build -t face-tracking-backend .

# Run container
docker run -d -p 8000:8000 --env-file .env face-tracking-backend
```

## 📚 API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### Authentication
- `POST /auth/login/` - User login
- `GET /auth/secure/` - Protected endpoint test
- `GET /auth/role-protected/` - Admin-only endpoint test
- `POST /auth/users/` - Create user (admin)
- `PATCH /auth/users/{user_id}/status` - Update user status (admin)

#### Streaming
- `GET /stream/{camera_id}` - MJPEG video stream
- `GET /stream/status/{camera_id}` - Camera status
- `GET /stream/` - Overall streaming status

#### Employees
- `GET /employees/` - List all employees
- `GET /employees/{employee_id}` - Get specific employee
- `POST /employees/` - Create employee (admin)
- `PUT /employees/{employee_id}` - Update employee (admin)
- `DELETE /employees/{employee_id}` - Delete employee (admin)

#### Attendance
- `GET /attendance/` - Get latest attendance records
- `GET /attendance/{employee_id}` - Get attendance by employee

#### Face Embeddings
- `POST /embeddings/enroll/` - Enroll employee faces (admin)
- `POST /embeddings/add/` - Add single face embedding (admin)
- `DELETE /embeddings/delete_all/{employee_id}` - Delete all embeddings (admin)
- `POST /embeddings/archive_all/{employee_id}` - Archive all embeddings (admin)

## 🔐 Security Features

### Authentication
- JWT tokens with configurable expiration
- Role-based access control (admin/user roles)
- Rate limiting on login attempts
- Secure password hashing with bcrypt

### API Security
- CORS protection with configurable origins
- Request logging and monitoring
- Input validation with Pydantic models
- SQL injection protection via SQLAlchemy ORM

### Production Security Recommendations
1. Use HTTPS only
2. Set strong JWT secret keys
3. Configure proper CORS origins
4. Implement API rate limiting
5. Regular security updates
6. Database connection encryption
7. Firewall configuration

## 📊 Monitoring & Logging

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors requiring immediate attention

### Log Files
- Location: `logs/app.log`
- Rotation: Daily with 30-day retention
- Format: Timestamp | Level | Module | Message

### Monitoring Endpoints
- Health check: `GET /`
- Stream status: `GET /stream/`
- Camera status: `GET /stream/status/{camera_id}`

## 🛠️ Development

### Project Structure
```
backend/
├── app/                    # FastAPI application
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration management
│   ├── dependencies.py    # Shared dependencies
│   └── routers/           # API route handlers
├── core/                  # Core face tracking logic
│   ├── fts_system.py      # Face tracking pipeline
│   └── face_enroller.py   # Face enrollment management
├── db/                    # Database components
│   ├── db_config.py       # Database configuration
│   ├── db_models.py       # SQLAlchemy models
│   └── db_manager.py      # Database operations
├── utils/                 # Utility modules
│   ├── security.py        # Authentication utilities
│   └── logging.py         # Logging configuration
├── tasks/                 # Background tasks
│   └── camera_tasks.py    # Camera monitoring tasks
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── start.py              # Startup script
```

### Adding New Features
1. Create router in `app/routers/`
2. Add database models in `db/db_models.py`
3. Update database manager in `db/db_manager.py`
4. Add authentication if needed using `utils/security.py`
5. Update configuration in `app/config.py`
6. Include router in `app/main.py`

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 🚀 Deployment

### Company Server Deployment

#### Option 1: Direct Deployment
```bash
# On server
git clone <repository>
cd face-tracking-system/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with production settings

# Run with systemd service
sudo systemctl enable face-tracking-backend
sudo systemctl start face-tracking-backend
```

#### Option 2: Docker Deployment
```bash
# Build and deploy
docker build -t face-tracking-backend .
docker run -d --name fts-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  face-tracking-backend
```

#### Option 3: Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: face_tracking
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Reverse Proxy Setup (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /stream/ {
        proxy_pass http://localhost:8000/stream/;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

## 📈 Performance Optimization

### Database Optimization
- Use connection pooling
- Implement database indexing
- Regular VACUUM operations
- Monitor query performance

### Face Recognition Optimization
- Adjust `FACE_RECOGNITION_TOLERANCE`
- Use `hog` model for speed, `cnn` for accuracy
- Implement face embedding caching
- Process every nth frame for real-time performance

### Streaming Optimization
- Limit concurrent streams
- Adjust frame rate based on hardware
- Implement adaptive quality settings
- Use hardware acceleration if available

## 🐛 Troubleshooting

### Common Issues

#### Camera Access Issues
```bash
# Check camera permissions
ls -l /dev/video*
sudo usermod -a -G video $USER

# Test camera
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d face_tracking
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x start.py
chown -R $USER:$USER logs/
mkdir -p uploads face_images
```

#### Memory Issues
- Reduce `MAX_CONCURRENT_STREAMS`
- Adjust worker processes
- Monitor with `htop` or `top`
- Consider hardware upgrade

### Log Analysis
```bash
# View real-time logs
tail -f logs/app.log

# Search for errors
grep "ERROR" logs/app.log

# Monitor specific user
grep "user123" logs/app.log
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Contact the development team

---

**Note**: This system is designed for company internal use. Ensure compliance with privacy regulations and company policies when deploying face recognition systems.