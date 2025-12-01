# 🛡️ CyberShield - AI-Powered Safe Chat Environment

> **Advanced Real-time Chat Application with AI-Driven Content Moderation and Mental Health Support.**

CyberShield is a cutting-edge communication platform designed to create a safe digital space. It leverages advanced Artificial Intelligence to detect cyberbullying, hate speech, and NSFW content in real-time, intervening automatically to protect users.

---

## 🌟 Key Features

### 1. 🤖 AI Content Moderation
- **Real-time Text Analysis**: Uses **Groq API (Llama 3)** to analyze every message for toxicity, hate speech, and harassment.
- **Image Safety**: Integrates **HuggingFace (Falconsai/nsfw_image_detection)** to detect and blur NSFW or inappropriate images.
- **Immediate Feedback**: Messages are flagged instantly, and users are warned before they can cause harm.

### 2. 🚨 CyberBOT Warning System
- **Automated Intervention**: A system bot that monitors conversations.
- **Warning Protocol**:
  - **1st-2nd Violation**: Warning message with educational context.
  - **3rd Violation**: **Red Tag** applied to the user's profile.
  - **5th Violation**: Account is automatically **Blocked**.
- **Separate Warning Channel**: CyberBOT opens a private chat with the violator to deliver warnings without disrupting the main conversation flow.

### 3. 🏷️ Red Tag System
- **Visual Indicator**: Users with a history of violations are marked with a **Red Tag** (⚠️).
- **Visibility**: The tag is visible to all other users in the chat header and conversation list, serving as a caution.

### 4. 👮 Admin Dashboard
- **Comprehensive Oversight**: Admins can view all active incidents, user reports, and system statistics.
- **User Management**: Ability to manually Block, Unblock, or Red Tag users.
- **Incident Logs**: Detailed logs of every violation, including the detected content, severity score, and AI analysis.

### 5. 🧠 Mental Health Support
- **AI Counselor**: A dedicated space for users to talk to an AI support assistant.
- **Resources**: Access to mental health resources and guidelines.

---

## 🏗️ System Architecture

CyberShield follows a modern client-server architecture with specialized AI microservices integration.

```mermaid
graph TD
    subgraph Client Side
        User[User Browser]
        Admin[Admin Browser]
    end

    subgraph Frontend [React + Vite + Material UI]
        UI[User Interface]
        WS_Client[WebSocket Client]
        State[State Management]
    end

    subgraph Backend [FastAPI + Python]
        API[REST API Endpoints]
        WS_Server[WebSocket Manager]
        Auth[JWT Authentication]
        Logic[Business Logic]
    end

    subgraph Data & AI
        DB[(SQLite Database)]
        Groq[Groq AI API\n(Text Analysis)]
        HF[HuggingFace API\n(Image Analysis)]
    end

    User <--> UI
    Admin <--> UI
    UI <--> WS_Client
    WS_Client <-->|WebSocket (Real-time)| WS_Server
    UI <-->|HTTP/REST| API
    
    API --> Logic
    WS_Server --> Logic
    Logic --> Auth
    Logic --> DB
    
    Logic -->|Async Request| Groq
    Logic -->|Async Request| HF
```

---

## 📂 Project Structure

```
CyberShield/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # API Route Handlers
│   │   │   └── v1/         # Version 1 Endpoints (Auth, Chat, Admin)
│   │   ├── core/           # Core Config (DB, Security, Settings)
│   │   ├── models/         # SQLAlchemy Database Models
│   │   ├── schemas/        # Pydantic Data Schemas
│   │   ├── services/       # Business Logic Services
│   │   │   ├── ai_detection.py  # AI Integration Logic
│   │   │   └── cyberbot.py      # CyberBOT Warning Logic
│   │   └── main.py         # Application Entry Point
│   ├── evidence/           # Stored Evidence Logs
│   ├── requirements.txt    # Python Dependencies
│   └── cybershield.db      # SQLite Database
│
└── safe-haven-chat/        # React Frontend
    ├── src/
    │   ├── components/     # Reusable UI Components
    │   ├── hooks/          # Custom React Hooks (useWebSocket)
    │   ├── pages/          # Application Pages (Chat, Login, Admin)
    │   ├── lib/            # Utilities (API Client)
    │   └── App.tsx         # Main Component
    └── package.json        # Node Dependencies
```

---

## 🧠 Core Logic & Implementation

### 🔐 Authentication
- **JWT (JSON Web Tokens)**: Used for secure, stateless authentication.
- **Hashing**: Passwords are hashed using `bcrypt` before storage.
- **Token Expiry**: Access tokens have a configurable expiry (default 24h) to ensure security.

### 📡 Real-time Communication
- **WebSockets**: The chat relies on persistent WebSocket connections for instant message delivery.
- **Connection Management**: The frontend `useWebSocket` hook handles connection, reconnection (with fresh tokens), and message dispatching.
- **Event Types**:
  - `message`: Standard user message.
  - `cyberbot_warning`: System warning from CyberBOT.
  - `typing`: Typing indicators.

### 🛡️ AI Detection Pipeline
1.  **Interception**: Every message sent via WebSocket is intercepted by the backend.
2.  **Analysis**:
    - **Text**: Sent to Groq API. The model analyzes the sentiment and checks for specific categories (harassment, hate speech, self-harm).
    - **Image**: Sent to HuggingFace API. The model returns a probability score for NSFW content.
3.  **Decision**:
    - If `Severity > Threshold`: The message is flagged.
    - **Incident Created**: Logged in the database.
    - **CyberBOT Triggered**: Warning sent to the user.

### 🤖 CyberBOT Logic
- **State Tracking**: Tracks `warning_count` for each user.
- **Escalation**:
  - `count >= 3`: Sets `has_red_tag = True`.
  - `count >= 5`: Sets `is_blocked = True`.
- **Feedback**: Sends a structured system message to the user explaining *why* they were flagged.

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Groq API Key
- HuggingFace API Token (Optional, for image detection)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env
echo "HF_TOKEN=your_token_here" >> .env

# Run Server
uvicorn main:app --reload
```
*The backend runs on `http://localhost:8000`*

### 2. Frontend Setup
```bash
cd safe-haven-chat
npm install

# Run Client
npm run dev
```
*The frontend runs on `http://localhost:8080` (or similar)*

### 3. Default Admin Account
The system automatically creates a default admin account on startup:
- **Username**: `admin`
- **Email**: `admin@cybershield.com`
- **Password**: `admin123`

---

## 📊 Use Cases

```mermaid
usecaseDiagram
    actor "User" as U
    actor "Admin" as A
    actor "CyberBOT" as CB

    package "CyberShield System" {
        usecase "Send/Receive Messages" as UC1
        usecase "Report Content" as UC2
        usecase "Receive Warnings" as UC3
        usecase "View Red Tags" as UC4
        
        usecase "Monitor Incidents" as UC5
        usecase "Ban/Unban Users" as UC6
        usecase "Analyze Content" as UC7
    }

    U --> UC1
    U --> UC2
    U --> UC4
    
    CB --> UC3
    CB --> UC7
    
    A --> UC5
    A --> UC6
    
    UC1 ..> UC7 : Triggers AI
    UC7 ..> UC3 : If Violation
```

---

## 🔮 Future Roadmap
- [ ] **Voice Analysis**: Real-time audio toxicity detection.
- [ ] **End-to-End Encryption**: Enhanced privacy for private chats.
- [ ] **Mobile App**: Native iOS and Android applications.
- [ ] **Advanced Analytics**: Heatmaps of cyberbullying trends.

---

**CyberShield** - *Protecting the Digital Conversation.*
