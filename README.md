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

---

# 📚 Detailed File Reference & Logic Explanation

This section provides a deep dive into every key file in the project, explaining its purpose, logic, and including critical code snippets.

## 🖥️ Backend (`backend/app/`)

### 1. `main.py` - Application Entry Point
**Purpose**: Initializes the FastAPI application, sets up CORS, database tables, and static admin user.
**Key Logic**:
- **Lifespan Manager**: Handles startup tasks like creating DB tables and the default admin user.
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    # Initialize admin user logic...
    yield
```

### 2. `services/ai_detection.py` - AI Content Analysis
**Purpose**: The brain of the system. Handles text and image analysis using external APIs.
**Key Logic**:
- **Text Analysis**: Sends content to Groq API (Llama 3) with a system prompt to classify toxicity.
```python
async def detect_abuse(text: str) -> dict:
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "Analyze for: cyberbullying, hate_speech, sexual_content..."},
            {"role": "user", "content": text}
        ]
    )
    # Returns JSON with severity and categories
```

### 3. `services/cyberbot.py` - Automated Warning System
**Purpose**: Manages automated interventions for policy violations.
**Key Logic**:
- **Warning Templates**: Context-aware messages based on violation type.
- **Escalation**: Auto-tags or blocks users based on `warning_count`.
```python
async def send_warning(self, db, user_id, violation_type, severity, categories):
    # Increment warning count
    user.warning_count += 1
    
    # Auto Red Tag logic
    if user.warning_count >= 3:
        user.has_red_tag = True
        
    # Generate and save warning message
    message = Message(
        sender_id=0,  # CyberBOT ID
        content=warning_text,
        message_type="system_warning"
    )
```

### 4. `api/v1/websocket.py` - Real-time Chat Handler
**Purpose**: Manages WebSocket connections and message routing.
**Key Logic**:
- **Connection Manager**: Tracks active user connections.
- **Message Pipeline**: Receive -> AI Check -> Save -> Broadcast.
```python
async def handle_message(data, sender, db):
    # 1. AI Detection
    detection_result = await ai_service.detect_abuse(content)
    
    # 2. If Flagged
    if detection_result["is_flagged"]:
        # Send CyberBOT warning
        await cyberbot_service.send_warning(...)
        
    # 3. Broadcast to receiver
    await manager.send_personal_message(message_data, receiver_id)
```

### 5. `models/user.py` - Database Schema
**Purpose**: Defines the User table structure.
**Key Logic**:
- **Fields**: `has_red_tag`, `warning_count`, `is_blocked` for safety features.
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    has_red_tag = Column(Boolean, default=False)  # Visual warning for others
    warning_count = Column(Integer, default=0)    # Tracks violations
```

---

## 🎨 Frontend (`safe-haven-chat/src/`)

### 1. `pages/Chat.tsx` - Main Chat Interface
**Purpose**: The core messaging UI. Handles real-time updates and user interactions.
**Key Logic**:
- **WebSocket Integration**: Connects to backend for live messages.
- **CyberBOT Handling**: Special logic to display system warnings.
```typescript
// Handling CyberBOT messages
if (wsMsg.type === 'cyberbot_warning' && wsMsg.sender_id === 0) {
  // Add to CyberBOT conversation view
  setMessages(prev => [...prev, systemMessage]);
  // Refresh conversation list to show new alert
  loadUserAndConversations();
}
```
- **Red Tag Display**: Shows warning badge for flagged users.
```typescript
{activePeer.has_red_tag && (
  <Tooltip title="Red Tagged User">
    <Box sx={{ bgcolor: 'error.main' }}>⚠️ RED TAG</Box>
  </Tooltip>
)}
```

### 2. `hooks/useWebSocket.ts` - Custom WebSocket Hook
**Purpose**: Manages the WebSocket connection lifecycle.
**Key Logic**:
- **Auto-Reconnect**: Automatically reconnects with fresh tokens if disconnected.
- **Message Routing**: Dispatches incoming messages to the correct handler.
```typescript
const connect = useCallback(() => {
  // Always get fresh token from storage
  const token = sessionStorage.getItem('auth_token');
  const ws = new WebSocket(`${wsHost}/api/v1/ws/chat/${token}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'cyberbot_warning') {
      // Handle warning
    }
  };
}, []);
```

### 3. `pages/Admin.tsx` - Admin Dashboard
**Purpose**: Control center for moderators.
**Key Logic**:
- **Data Visualization**: Charts for incidents and user stats.
- **Action Handlers**: Functions to Block/Unblock or Tag users.
```typescript
const handleToggleBlock = async (userId: number, currentStatus: boolean) => {
  await apiClient.updateUserBlockStatus(userId, !currentStatus);
  // Refresh list
  loadUsers();
};
```

### 4. `lib/api.ts` - API Client
**Purpose**: Centralized Axios instance for all HTTP requests.
**Key Logic**:
- **Interceptors**: Automatically adds JWT token to headers.
- **Error Handling**: Global error management.
```typescript
apiClient.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 5. `components/CyberbullyingAlertDialog.tsx`
**Purpose**: Popup alert when a user receives a flagged message.
**Key Logic**:
- **User Choice**: Allows victim to Report, Block, or Ignore.
```typescript
<Dialog open={open}>
  <DialogTitle>⚠️ Potential Cyberbullying Detected</DialogTitle>
  <DialogContent>
    This message was flagged by our AI. How would you like to proceed?
  </DialogContent>
  <DialogActions>
    <Button onClick={handleBlock} color="error">Block User</Button>
    <Button onClick={handleReport}>Report</Button>
  </DialogActions>
</Dialog>
```
