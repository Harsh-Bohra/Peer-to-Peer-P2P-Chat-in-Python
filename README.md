# P2P Chat Application

A robust peer-to-peer chat application built with Python, featuring real-time messaging, user authentication, and distributed architecture.

![P2P Chat](https://img.shields.io/badge/P2P-Chat-blue)
![Python](https://img.shields.io/badge/Python-3.x-green)
![License](https://img.shields.io/badge/License-MIT-orange)

## Features

- 🔒 Secure user authentication and registration
- 💬 Real-time peer-to-peer messaging
- 👥 Online user presence detection
- 🔄 Automatic reconnection handling
- 🎨 Modern PyQt5-based GUI
- 📱 Multi-client support
- 🔍 User search functionality
- 📊 Efficient binary packet protocol

## Architecture

### Components

1. **Registry Server**
   - Central authentication and user management
   - TCP port 3131 for client connections
   | UDP port 5151 for heartbeat messages
   - Maintains online user list

2. **Peer Clients**
   - Direct P2P communication
   - Dynamic port allocation (5858+)
   - Real-time message delivery
   - User presence management

### Network Protocol

```
Client -> Server (TCP 3131):
- Register: type=0, username, password
- Login: type=1, username, password
- Logout: type=3, username, "LOGOUT"
- Search: type=2, username, search_name
- All Online: type=4, username, "All"

Client -> Server (UDP 5151):
- Heartbeat: type=5, username, "HELLO"

Client -> Client (TCP 5858+):
- Message: type=0, username, message
- Request: type=1, username, "CHAT REQUEST"
- Notify: type=1, username, "New User"
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/p2p-chat-application.git
cd p2p-chat-application
```

2. Install dependencies:
```bash
pip install PyQt5
```

3. Run the application:

Start the server:
```bash
cd /path/to/project
PYTHONPATH=/path/to/project python3 Registryside/registry.py
```

Start a client:
```bash
cd /path/to/project
PYTHONPATH=/path/to/project python3 Peerside/login_screen.py
```

## Usage

1. **Registration**
   - Launch the client application
   - Enter username (min 3 characters)
   - Enter password (min 6 characters)
   - Click "Register"

2. **Login**
   - Enter registered credentials
   - Click "Login"

3. **Chatting**
   - View online users
   - Connect to peers using their IP and port
   - Send and receive messages in real-time

4. **Logout**
   - Click "Logout" to end session
   - Application will clean up resources




## Acknowledgments

- PyQt5 for the GUI framework
- Python's socket library for network communication
- All contributors who have helped improve this project
