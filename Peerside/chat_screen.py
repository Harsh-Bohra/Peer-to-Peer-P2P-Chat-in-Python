from core import constants as cn
import struct
from Peerside.ServerChannel import *
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCharFormat, QTextCursor
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from socket import *
import threading
import time
import sys
import subprocess
from datetime import datetime

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

global flagQ

log = cn.getlog()

class PeerOperation(QObject):
    # Define signals for UI updates
    error_signal = pyqtSignal(str)
    message_signal = pyqtSignal(str, str, str)
    
    def __init__(self, username, password, channel, gi):
        super().__init__()
        self.username = username
        self.password = password
        self.channel = channel
        self.gi = gi
        self.chat_list = set()
        self.flagQ = [0, 0]
        self.udp_thread = None
        self.udp_running = False
        self.tcp_thread = None
        self.tcp_running = False
        
        # Connect signals to slots
        self.error_signal.connect(self.gi.showError)
        self.message_signal.connect(self.gi.append_message)
        
        self.initilaze()

    def initilaze(self):
        try:
            listen_thread = threading.Thread(target=self.listen_server)
            listen_thread.daemon = True
            listen_thread.start()
        except Exception as e:
            log.error(f"Failed to initialize chat: {str(e)}")
            self.error_signal.emit("Failed to initialize chat. Please try logging in again.")

    def listen_server(self):
        try:
            port = 5858
            while True:
                try:
                    serverSocket = socket(AF_INET, SOCK_STREAM)
                    serverSocket.bind(('', port))
                    serverSocket.listen(1)
                    hostname = gethostname()
                    local_ip = gethostbyname(hostname)
                    log.info(f"Server is listening on tcp [  , {port} ]")
                    self.message_signal.emit("System", f"Your chat is listening on port: {port}\nOthers can connect to you using:\nIP: {local_ip}\nPort: {port}", "system")
                    break
                except OSError as e:
                    if e.errno == 48 or (hasattr(e, 'winerror') and e.winerror == 10048):
                        port += 1
                        continue
                    raise e

            while True:
                connectionSocket, addr = serverSocket.accept()
                log.info(f"Connection accepted from {addr[0]}")
                self.handle_connection(connectionSocket, addr)
        except Exception as e:
            log.error(f"Error setting up chat server: {str(e)}")
            self.error_signal.emit("Failed to start chat server")

    def handle_connection(self, connectionSocket, addr):
        try:
            while True:
                packet = connectionSocket.recv(1024)
                if not packet:
                    break
                typ, username, message = struct.unpack('b 10s 100s', packet)
                username = self.purge(username)
                message = self.purge(message)
                self.message_signal.emit(username, message, "received")
        except Exception as e:
            log.error(f"Error handling connection: {str(e)}")
        finally:
            connectionSocket.close()

    def send_messages(self):
        try:
            message = self.gi.getMessage()
            if not message:
                return
            
            self.message_signal.emit("Me", message, "sent")
            
            if self.send_message(message):
                log.info(f"Message sent successfully: {message}")
            else:
                self.error_signal.emit("Failed to send message to some peers")
        except Exception as e:
            log.error(f"Error in send_messages: {str(e)}")
            self.error_signal.emit("Failed to send message")

    def send_message(self, message):
        try:
            success = True
            failed_peers = set()
            
            for peer_ip, peer_port in self.chat_list:
                try:
                    s = socket(AF_INET, SOCK_STREAM)
                    s.settimeout(5)  # 5 second timeout
                    s.connect((peer_ip, peer_port))
                    packet = struct.pack('b 10s 100s', 0, bytes(self.username, 'utf-8'), bytes(message, 'utf-8'))
                    s.send(packet)
                    s.close()
                except Exception as e:
                    log.error(f"Failed to send message to {peer_ip}:{peer_port}: {str(e)}")
                    failed_peers.add((peer_ip, peer_port))
                    success = False
            
            # Remove failed peers from chat list
            self.chat_list -= failed_peers
            return success
        except Exception as e:
            log.error(f"Error sending message: {str(e)}")
            return False

    def connect_peer(self, ip, port):
        try:
            s = socket(AF_INET, SOCK_STREAM)
            s.settimeout(5)  # 5 second timeout
            s.connect((ip, int(port)))
            log.info(f"Connected to peer {ip}:{port}")
            s.close()
            self.chat_list.add((ip, int(port)))  # Add peer with its port to chat list
            return True
        except Exception as e:
            log.error(f"Failed to connect to peer {ip}:{port}: {str(e)}")
            self.error_signal.emit(f"Failed to connect to peer {ip}:{port}")
            return False

    def send_request_to_peer(self):
        try:
            ip = self.gi.getIp()
            port = self.gi.getPort()
            
            if not ip or not port:
                self.error_signal.emit("Please enter IP and Port")
                return
                
            if self.connect_peer(ip, port):
                self.gi.showMessageBox("Connected successfully!")
                self.chat_list.add((ip, int(port)))
        except Exception as e:
            log.error(f"Error in send_request_to_peer: {str(e)}")
            self.error_signal.emit("Failed to send request to peer")

    def purge(self, message):
        message = message.decode('utf-8')
        index = message.find('\x00')
        if index != -1:
            return message[0:index]
        return message

    def refreshOnline(self):
        try:
            self.gi.textBrowser.clear()
            self.gi.textBrowser.append("Welcome to P2P Chat!")
            self.gi.textBrowser.append("-------------------")
            self.gi.textBrowser.append("To start chatting:")
            self.gi.textBrowser.append("1. Click on a user to start a chat")
            self.gi.textBrowser.append("2. Type your message and press Enter")
            self.gi.textBrowser.append("3. Click Logout when done")
            log.info("Welcome message displayed")
        except Exception as e:
            log.error(f"Error displaying welcome message: {str(e)}")
            self.error_signal.emit("Failed to display welcome message")

    def logout(self):
        try:
            # First try to logout from the server
            result = self.channel.send_request(3, self.username, self.password, "LOGOUT")
            if result[0] in [23, 25, 45]:  # Accept both 23 and 25 as successful logout
                log.info(f"Logged out successfully: {self.username}")
                # Show the login screen again
                subprocess.Popen(['python', '-m', 'Peerside.login_screen'])
                # Close the chat window and exit
                self.gi.close()
                sys.exit(0)
            else:
                log.error(f"Logout failed: {result[1]}")
                self.error_signal.emit("Failed to logout properly")
        except Exception as e:
            log.error(f"Error during logout: {str(e)}")
            self.error_signal.emit("Failed to logout")

    def showError(self, message):
        self.error_signal.emit(message)

    def start_udp_thread(self):
        if self.udp_thread is not None and self.udp_thread.is_alive():
            log.warning("UDP thread is already running")
            return
            
        self.udp_running = True
        self.udp_thread = threading.Thread(target=self.udp_broadcast)
        self.udp_thread.daemon = True
        self.udp_thread.start()
        log.info("UDP broadcast thread started")

    def stop_udp_thread(self):
        self.udp_running = False
        if self.udp_thread:
            self.udp_thread.join(timeout=2)
            self.udp_thread = None
        log.info("UDP broadcast thread stopped")

    def udp_broadcast(self):
        try:
            s = socket(AF_INET, SOCK_DGRAM)
            s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            s.bind(('', 0))
            
            while self.udp_running:
                try:
                    packet = struct.pack('b 10s', 1, bytes(self.username, 'utf-8'))
                    s.sendto(packet, ('<broadcast>', 5858))
                    time.sleep(1)
                except Exception as e:
                    log.error(f"Error in UDP broadcast: {str(e)}")
                    time.sleep(1)
                    
        except Exception as e:
            log.error(f"Fatal error in UDP broadcast thread: {str(e)}")
        finally:
            try:
                s.close()
            except:
                pass
            log.info("UDP broadcast thread terminated")

    def Onay(self):
        try:
            global flagQ
            if flagQ[0] is not None:
                self.chat_list.add(flagQ[0])
                self.gi.showMessageBox(f"Connected to {flagQ[0]}")
                self.gi.onayB.setVisible(False)
                self.gi.retB.setVisible(False)
                flagQ = [None, 0]
        except Exception as e:
            log.error(f"Error in Onay: {str(e)}")
            self.error_signal.emit("Failed to accept chat request")

    def Ret(self):
        try:
            global flagQ
            self.gi.onayB.setVisible(False)
            self.gi.retB.setVisible(False)
            flagQ = [None, 0]
        except Exception as e:
            log.error(f"Error in Ret: {str(e)}")
            self.error_signal.emit("Failed to reject chat request")

    def append_message(self, username, message, message_type):
        self.message_signal.emit(username, message, message_type)


class Ui_ChatScreen(QtWidgets.QDialog):

    def __init__(self, username, password, channel):
        super().__init__()
        self.username = username
        self.password = password
        self.channel = channel
        self.peer = PeerOperation(username=username, password=password, channel=channel, gi=self)

    def append_message(self, sender, message, message_type):
        timestamp = datetime.now().strftime("%H:%M")
        text = f"[{timestamp}] {sender}: {message}\n"
        
        # Format for different message types
        if message_type == "sent":
            self.tb_chatscreen.append(f'<span style="color: #0084ff">{text}</span>')
        elif message_type == "received":
            self.tb_chatscreen.append(f'<span style="color: #ff3b30">{text}</span>')
        else:  # system message
            self.tb_chatscreen.append(f'<span style="color: #8e8e93">{text}</span>')
        
        self.tb_chatscreen.verticalScrollBar().setValue(
            self.tb_chatscreen.verticalScrollBar().maximum()
        )

    def chatR(self,name):
        self.onayB.setVisible(True)
        self.retB.setVisible(True)
        global flagQ
        flagQ = [name, 0]
        print("Chat geldi")
        self.onaytext.setText("Chat request: "+str(name[0]))

    def getIp(self):
        return self.te_ip.text()

    def getPort(self):
        return int(self.te_port.text())

    def getMessage(self):
        mess = self.te_message.toPlainText().strip()
        self.te_message.clear()
        return mess

    def setupUi(self, ChatScreen):
        ChatScreen.setObjectName(_fromUtf8("ChatScreen"))
        ChatScreen.resize(1000, 750)
        ChatScreen.setMinimumSize(1000, 750)
        ChatScreen.setMaximumSize(1000, 750)
        
        # Set window style
        ChatScreen.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #1a1a1a;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #e4e6eb;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                color: black;
            }
            QLineEdit:focus {
                border-color: #1877f2;
            }
            QTextEdit {
                padding: 10px;
                border: 2px solid #e4e6eb;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                color: black;
            }
            QTextEdit:focus {
                border-color: #1877f2;
            }
            QPushButton {
                padding: 10px;
                border: none;
                border-radius: 8px;
                background-color: #1877f2;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #166fe5;
            }
            QPushButton:pressed {
                background-color: #1459b3;
            }
            QTextBrowser {
                border: 2px solid #e4e6eb;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
                font-size: 14px;
                color: black;
            }
        """)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget(ChatScreen)
        ChatScreen.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Connection section
        connection_layout = QtWidgets.QHBoxLayout()
        
        # IP input
        ip_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(ChatScreen)
        self.label.setText("IP:")
        self.label.setFixedWidth(40)
        ip_layout.addWidget(self.label)
        
        self.te_ip = QtWidgets.QLineEdit(ChatScreen)
        self.te_ip.setFixedHeight(40)
        self.te_ip.setPlaceholderText("Enter IP address")
        ip_layout.addWidget(self.te_ip)
        connection_layout.addLayout(ip_layout)

        # Port input
        port_layout = QtWidgets.QHBoxLayout()
        self.label_2 = QtWidgets.QLabel(ChatScreen)
        self.label_2.setText("Port:")
        self.label_2.setFixedWidth(40)
        port_layout.addWidget(self.label_2)
        
        self.te_port = QtWidgets.QLineEdit(ChatScreen)
        self.te_port.setFixedHeight(40)
        self.te_port.setPlaceholderText("Enter port")
        port_layout.addWidget(self.te_port)
        connection_layout.addLayout(port_layout)

        # Connect button
        self.btn_connect = QtWidgets.QPushButton(ChatScreen)
        self.btn_connect.setFixedHeight(40)
        self.btn_connect.setText("Connect")
        connection_layout.addWidget(self.btn_connect)

        layout.addLayout(connection_layout)

        # Main chat area
        chat_layout = QtWidgets.QHBoxLayout()
        
        # Chat messages
        self.tb_chatscreen = QtWidgets.QTextBrowser(ChatScreen)
        self.tb_chatscreen.setReadOnly(True)
        chat_layout.addWidget(self.tb_chatscreen, stretch=2)

        # Online users
        users_layout = QtWidgets.QVBoxLayout()
        users_label = QtWidgets.QLabel(ChatScreen)
        users_label.setAlignment(Qt.AlignCenter)
        users_layout.addWidget(users_label)
        
        self.textBrowser = QtWidgets.QTextBrowser(ChatScreen)
        self.textBrowser.setReadOnly(True)
        users_layout.addWidget(self.textBrowser)
        
        self.btn_refresh = QtWidgets.QPushButton(ChatScreen)
        self.btn_refresh.setFixedHeight(40)
        self.btn_refresh.setText("Refresh")
        users_layout.addWidget(self.btn_refresh)
        
        chat_layout.addLayout(users_layout, stretch=1)
        layout.addLayout(chat_layout)

        # Message input
        message_layout = QtWidgets.QHBoxLayout()
        
        self.te_message = QtWidgets.QTextEdit(ChatScreen)
        self.te_message.setFixedHeight(60)
        self.te_message.setPlaceholderText("Type your message...")
        message_layout.addWidget(self.te_message)
        
        self.btn_send = QtWidgets.QPushButton(ChatScreen)
        self.btn_send.setFixedHeight(60)
        self.btn_send.setText("Send")
        message_layout.addWidget(self.btn_send)
        
        layout.addLayout(message_layout)

        # Logout button
        self.btn_logout = QtWidgets.QPushButton(ChatScreen)
        self.btn_logout.setFixedHeight(40)
        self.btn_logout.setText("Logout")
        layout.addWidget(self.btn_logout)

        # Chat request buttons
        request_layout = QtWidgets.QHBoxLayout()
        
        self.onaytext = QtWidgets.QLabel(ChatScreen)
        self.onaytext.setAlignment(Qt.AlignCenter)
        request_layout.addWidget(self.onaytext)
        
        self.onayB = QtWidgets.QPushButton(ChatScreen)
        self.onayB.setFixedHeight(40)
        self.onayB.setText("Accept")
        request_layout.addWidget(self.onayB)
        
        self.retB = QtWidgets.QPushButton(ChatScreen)
        self.retB.setFixedHeight(40)
        self.retB.setText("Reject")
        request_layout.addWidget(self.retB)
        
        layout.addLayout(request_layout)

        # Connect signals
        self.btn_logout.clicked.connect(self.peer.logout)
        self.btn_send.clicked.connect(self.peer.send_messages)
        self.btn_connect.clicked.connect(self.peer.send_request_to_peer)
        self.onayB.clicked.connect(self.peer.Onay)
        self.retB.clicked.connect(self.peer.Ret)
        self.btn_refresh.clicked.connect(self.peer.refreshOnline)

        # Initialize
        self.onayB.setVisible(False)
        self.retB.setVisible(False)
        self.peer.refreshOnline()

        self.retranslateUi(ChatScreen)
        QtCore.QMetaObject.connectSlotsByName(ChatScreen)

    def retranslateUi(self, ChatScreen):
        ChatScreen.setWindowTitle(_translate("ChatScreen", "P2P Chat Application", None))
        self.btn_send.setText(_translate("ChatScreen", "Send", None))
        self.label.setText(_translate("ChatScreen", "IP :", None))
        self.label_2.setText(_translate("ChatScreen", "PORT : ", None))
        self.btn_connect.setText(_translate("ChatScreen", "Connect", None))
        self.btn_refresh.setText(_translate("ChatScreen", "Refresh", None))
        self.btn_logout.setText(_translate("ChatScreen", "Logout", None))

    def listen(self):
        while True:
            time.sleep(1)

    def showMessageBox(self, message):
        QtWidgets.QMessageBox.information(self, "Message", message)

    def showError(self, message):
        QtWidgets.QMessageBox.critical(self, "Error", message)

class ChatScreen(QtWidgets.QMainWindow):
    def __init__(self, username, password, channel):
        super(ChatScreen, self).__init__()
        self.ui = Ui_ChatScreen()
        self.ui.setupUi(self)
        self.peer_operation = PeerOperation(username, password, channel, self.ui)
        self.setup_connections()
        
    def setup_connections(self):
        self.ui.btn_send.clicked.connect(self.peer_operation.send_messages)
        self.ui.btn_connect.clicked.connect(self.peer_operation.send_request_to_peer)
        self.ui.btn_refresh.clicked.connect(self.peer_operation.refreshOnline)
        self.ui.btn_logout.clicked.connect(self.peer_operation.logout)
        
    def closeEvent(self, event):
        try:
            # Clean up resources when window is closed
            self.peer_operation.logout()
            event.accept()
        except Exception as e:
            log.error(f"Error during window close: {str(e)}")
            event.accept()

    def showError(self, message):
        QtWidgets.QMessageBox.critical(self, "Error", message)
        
    def showMessageBox(self, message):
        QtWidgets.QMessageBox.information(self, "Message", message)
