# Jo Yuri Image Recognition System

A semantic image search and face verification system for Jo Yuri (IZ*ONE).

## Features (wip)

- **Semantic Search**: Query images by description ("smiling", "standing", "concert outfit")
- **Face Verification**: Detect if a new image contains Jo Yuri with confidence score
- **Image Scraping**: Collect images from Pinterest boards

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.11+) |
| Embeddings | CLIP (openai/clip) |
| Face Recognition | face_recognition (dlib) |
| Vector Database | Qdrant |
| Frontend | Next.js |
| Scraping | Playwright |

## Project Structure

```
jo-yuri/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── services/        # CLIP, face recognition, vector store
│   │   ├── models/          # Pydantic schemas
│   │   └── utils/           # Helper functions
│   ├── scripts/scraper/     # Pinterest scraper
│   └── data/
│       ├── images/          # Scraped images
│       └── reference/       # Jo Yuri reference faces
├── frontend/                # Next.js app
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for Qdrant)

### Setup

```bash
# Start Qdrant
docker-compose up -d qdrant

# Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the API
uvicorn app.main:app --reload
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/images/upload` | Upload and index an image |
| GET | `/api/search?q=smiling` | Semantic search |
| POST | `/api/verify` | Verify if image contains Jo Yuri |
| POST | `/api/scrape` | Trigger Pinterest scrape |

## Future Plans

- [ ] AWS deployment (S3, ECS Fargate)
- [ ] Fine-tuned model for higher accuracy
- [ ] Real-time video detection
