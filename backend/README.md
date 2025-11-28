# CyberShield Backend

FastAPI backend for the CyberShield Safe Haven Chat application.

## Features

- **Authentication**: JWT-based authentication with signup/login
- **Friend System**: Send/accept friend requests
- **Real-time Chat**: WebSocket-based messaging
- **AI Detection**: 
  - Groq LLM for text abuse detection
  - HuggingFace models for image/video NSFW detection
- **Evidence Logging**: Automatic screenshot and incident logging
- **Admin Dashboard**: Comprehensive admin panel for managing users, incidents, and reports
- **User Tagging**: Red tag system for users with harassment history

## Setup

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - GROQ_API_KEY: Get from https://console.groq.com
# - HF_TOKEN: Get from https://huggingface.co/settings/tokens
# - SECRET_KEY: Generate a random secret key
```

3. **Run the server**:
```bash
python main.py
# Or with uvicorn:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user info

### Friends
- `POST /api/v1/friends/request` - Send friend request
- `GET /api/v1/friends/requests` - Get all friend requests
- `GET /api/v1/friends/requests/received` - Get received requests
- `PUT /api/v1/friends/request/{id}` - Accept/reject request
- `GET /api/v1/friends/list` - Get friends list
- `GET /api/v1/friends/search?query=...` - Search users

### Messages
- `POST /api/v1/messages/send` - Send message (with AI detection)
- `POST /api/v1/messages/upload-image` - Upload and validate image
- `GET /api/v1/messages/conversation/{user_id}` - Get conversation
- `GET /api/v1/messages/conversations` - Get all conversations

### WebSocket
- `WS /api/v1/ws/chat/{token}` - Real-time chat connection

### Admin
- `GET /api/v1/admin/dashboard/stats` - Dashboard statistics
- `GET /api/v1/admin/incidents` - Get all incidents
- `PUT /api/v1/admin/incidents/{id}` - Update incident status
- `GET /api/v1/admin/reports` - Get all reports
- `PUT /api/v1/admin/reports/{id}` - Update report status
- `GET /api/v1/admin/users` - Get all users
- `PUT /api/v1/admin/users/{id}/tag` - Update user red tag
- `PUT /api/v1/admin/users/{id}/block` - Block/unblock user
- `GET /api/v1/admin/reports/generate` - Generate evidence report

## Database

SQLite database is created automatically. Tables:
- `users` - User accounts
- `friend_requests` - Friend request system
- `messages` - Chat messages
- `incidents` - Detected abuse incidents
- `reports` - User-generated reports

## AI Detection

### Text Detection (Groq)
- Uses Llama 3.3 70B model
- Detects: cyberbullying, harassment, hate speech, sexual content
- Returns severity level and filtered text

### Image Detection (HuggingFace)
- Uses Falconsai/nsfw_image_detection model
- Detects: NSFW, porn, nude, inappropriate content
- Blocks unsafe images from being sent

## Evidence Storage

Evidence is stored in:
- `./evidence/screenshots/` - Screenshot captures
- `./evidence/logs/` - JSON incident logs

## Environment Variables

See `.env.example` for all required variables.

## Development

The backend uses:
- FastAPI for REST API
- SQLAlchemy for ORM
- WebSockets for real-time communication
- JWT for authentication
- Groq for LLM
- HuggingFace Transformers for image detection

