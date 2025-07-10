# 🐦 Janawar Bird Census System

Janawar is an acoustic monitoring system for bird population census and analysis. It consists of edge devices that record bird sounds and a backend system that processes and analyzes the audio data using BirdNET.

## 🌟 Features

- **Audio Recording**: Capture high-quality bird vocalizations using edge devices
- **Species Identification**: Automatic bird species detection using BirdNET
- **Geolocation**: Track recording locations with GPS integration
- **Data Management**: Store and manage audio recordings and analysis results
- **RESTful API**: Comprehensive API for data access and management
- **Real-time Processing**: Process audio recordings in real-time
- **Scalable Architecture**: Designed to handle multiple edge devices

## 🏗️ System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Edge Device   │────▶│    Backend     │────▶│  Database      │
│  (Raspberry Pi) │     │   (FastAPI)     │     │  (PostgreSQL)  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🚀 Quick Start with Docker

The easiest way to get started is using Docker Compose:

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/janawar-census.git
   cd janawar-census
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Build and start the services**
   ```bash
   docker-compose up --build -d
   ```

4. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Admin Interface: http://localhost:8000/admin
   - Default Admin Credentials:
     - Email: admin@example.com
     - Password: changeme

## 🛠️ Manual Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- FFmpeg
- PortAudio
- BirdNET Models (automatically downloaded)

### Setup Instructions

1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix/macOS:
   source venv/bin/activate
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database**
   ```bash
   # Create database
   createdb janawar
   
   # Run migrations
   alembic upgrade head
   ```

4. **Download BirdNET models**
   ```bash
   python -m app.services.download_models
   ```

5. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📂 Project Structure

```
backend/
├── app/                    # Application package
│   ├── api/               # API routes
│   ├── core/              # Core functionality (config, security, etc.)
│   ├── db/                # Database configuration
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic models
│   ├── services/          # Business logic
│   │   └── audio_analysis.py  # BirdNET integration
│   └── main.py            # Application entry point
├── tests/                 # Test files
├── alembic/               # Database migrations
├── .env.example           # Example environment variables
└── requirements.txt       # Python dependencies
```

## 🌐 API Documentation

Once the application is running, you can access:

- **OpenAPI Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Environment Variables

Key environment variables (see `.env.example` for all options):

```
# Database
POSTGRES_USER=janawar
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=janawar

# Redis
REDIS_PASSWORD=your_redis_password

# Application
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development

# BirdNET
BIRDNET_MODEL_PATH=./birdnet_models/checkpoints/V2.4/BirdNET_GLOBAL_6K_V2.4_Model
BIRDNET_LABELS_PATH=./birdnet_models/checkpoints/V2.4/BirdNET_GLOBAL_6K_V2.4_Labels.txt
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [BirdNET](https://birdnet.cornell.edu/) - For the amazing bird sound recognition model
- [FastAPI](https://fastapi.tiangolo.com/) - For the high-performance web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - For the ORM
- [Alembic](https://alembic.sqlalchemy.org/) - For database migrations
   ```

6. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API documentation (Swagger UI) will be available at `http://localhost:8000/docs`

## 🏗️ Project Structure

```
backend/
├── app/                   # Application package
│   ├── api/               # API routes
│   ├── core/              # Core functionality (config, security, etc.)
│   ├── db/                # Database configuration
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic models
│   ├── services/          # Business logic
│   ├── utils/             # Utility functions
│   └── main.py            # Application entry point
├── tests/                 # Test files
├── alembic/               # Database migrations
├── .env.example           # Example environment variables
└── requirements.txt       # Python dependencies
```

## 📚 API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

To run the test suite:

```bash
pytest
```

## 🚀 Deployment

For production deployment, use Gunicorn with Uvicorn workers:

```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
