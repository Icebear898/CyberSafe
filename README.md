# CyberShield - Safe Haven Chat

A real-time AI-powered chat application with cyberbullying detection and mental health support.

## Features

- 🔒 **Real-time Cyberbullying Detection**: AI-powered content moderation using Groq LLM
- 💬 **Secure Messaging**: End-to-end encrypted chat with WebSocket support
- 🤖 **AI Mental Health Counselor**: 24/7 emotional support chatbot
- 👥 **Friend Management**: Add friends, manage connections, and control your network
- 🛡️ **Safety Features**: Content filtering, user blocking, and incident reporting
- 📊 **Admin Dashboard**: Comprehensive monitoring and management tools
- 🎨 **Modern UI**: Beautiful glassmorphism design with responsive layout

## Tech Stack

### Frontend
- React + TypeScript
- Material-UI (MUI)
- Tailwind CSS
- Framer Motion
- React Router
- WebSocket client

### Backend
- FastAPI (Python)
- SQLAlchemy + SQLite
- WebSocket server
- Groq AI API
- HuggingFace Transformers
- Passlib + JWT authentication

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Groq API key (get from https://console.groq.com)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

5. Run the server:
```bash
uvicorn main:app --reload
```

Backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd safe-haven-chat
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

Frontend will run on `http://localhost:8080`

### Create Admin Account

```bash
cd backend
source venv/bin/activate
python create_admin.py
```

Follow the prompts to create an admin account.

## Usage

1. **Sign Up**: Create a new account at `/signup`
2. **Login**: Access your account at `/login`
3. **Add Friends**: Navigate to Friends page to connect with others
4. **Start Chatting**: Select a friend and start messaging
5. **AI Counselor**: Access mental health support at `/mental-health`
6. **Admin Dashboard**: Login as admin and visit `/admin`

## Security Features

- Session-based authentication (tab-specific tokens)
- Password hashing with bcrypt
- Content filtering and moderation
- User blocking and reporting
- Red-tag system for repeat offenders
- Screenshot evidence collection

## Project Structure

```
Cybershield/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── core/           # Config and utilities
│   ├── create_admin.py     # Admin account creation
│   └── main.py             # Application entry point
│
└── safe-haven-chat/        # React frontend
    ├── src/
    │   ├── components/     # Reusable components
    │   ├── pages/          # Page components
    │   ├── lib/            # API client and utilities
    │   └── hooks/          # Custom React hooks
    └── index.html
```

## Contributing

This is a student project for cyberbullying prevention. Contributions are welcome!

## License

MIT License

## Acknowledgments

- Groq for AI API
- HuggingFace for ML models
- Material-UI for component library
