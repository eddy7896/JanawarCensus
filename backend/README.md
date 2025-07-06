# 🚀 Janawar Backend

This is the backend service for the Janawar Bird Acoustic Census System, built with FastAPI and PostgreSQL.

## 🛠️ Features

- RESTful API endpoints for bird observation data
- Real-time audio processing with BirdNET
- JWT-based authentication
- PostgreSQL database integration
- Async/await support
- OpenAPI documentation

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis (for caching)
- FFmpeg (for audio processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/janawar-census.git
   cd janawar-census/backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
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
├── app/                    # Application package
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
