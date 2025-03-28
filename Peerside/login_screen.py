import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt
from core import constants as cn
from Peerside.chat_screen import Ui_ChatScreen
import time

from Peerside.ServerChannel import *

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

LOG = cn.getlog()

class Ui_LoginScreen(object):
    def __init__(self, mychannel):
        self.mychannel = mychannel
        self.mychannel.connect()

    def register_request(self):
        uname = self.te_username.text().strip()
        passw = self.te_password.text().strip()

        if not uname or not passw:
            self.showMessageBox('Please enter both username and password')
            return

        if len(uname) < 3:
            self.showMessageBox('Username must be at least 3 characters long')
            return

        if len(passw) < 6:
            self.showMessageBox('Password must be at least 6 characters long')
            return

        result = self.mychannel.send_request(0, uname, passw, passw)
        if result[0] == 20:
            self.showMessageBox('Successfully Registered')
            LOG.info(f"You registered [{uname}, {passw}]")
            QtCore.QTimer.singleShot(1000, lambda: self.perform_login(uname, passw))
        else:
            LOG.error(f"Registration failed [{uname}, {passw}]")
            self.showMessageBox(f'Registration failed: {result[1]}')

    def perform_login(self, uname, passw):
        result = self.mychannel.send_request(1, uname, passw, passw)
        if result[0] == 21:
            LOG.info(f"You logged in [{uname}, {passw}]")
            self.open_chat()
        else:
            LOG.error(f"Login failed after registration [{uname}, {passw}]")
            self.showMessageBox(f'Registration successful but login failed: {result[1]}')

    def login_request(self):
        uname = self.te_username.text().strip()
        passw = self.te_password.text().strip()

        if not uname or not passw:
            self.showMessageBox('Please enter both username and password')
            return

        result = self.mychannel.send_request(1, uname, passw, passw)
        if result[0] == 21:
            LOG.info(f"You logged in [{uname}, {passw}]")
            self.open_chat()
        else:
            LOG.error(f"Login failed [{uname}, {passw}]")
            self.showMessageBox(f'Login failed: {result[1]}')

    def showMessageBox(self, message):
        try:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setWindowTitle('Message')
            msgBox.setText(message)
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.exec_()
        except Exception as e:
            LOG.error(f"Failed to show message box: {str(e)}")

    def open_chat(self):
        try:
            self.cwindow = QtWidgets.QMainWindow()
            self.ui = Ui_ChatScreen(self.te_username.text(), self.te_password.text(), self.mychannel)
            self.ui.setupUi(self.cwindow)
            MainWindow.hide()
            self.cwindow.show()
        except Exception as e:
            LOG.error(f"Failed to open chat window: {str(e)}")
            self.showMessageBox('Failed to open chat window. Please try logging in again.')

    def setupUi(self, LoginScreen):
        LoginScreen.setObjectName(_fromUtf8("LoginScreen"))
        LoginScreen.resize(400, 500)
        LoginScreen.setMinimumSize(400, 500)
        LoginScreen.setMaximumSize(400, 500)
        
        # Set window style
        LoginScreen.setStyleSheet("""
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
        """)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget(LoginScreen)
        LoginScreen.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        self.label_3 = QtWidgets.QLabel(LoginScreen)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.label_3.setFont(font)
        self.label_3.setAlignment(Qt.AlignCenter)
        self.label_3.setText("P2P Chat")
        layout.addWidget(self.label_3)

        # Add some spacing
        layout.addSpacing(20)

        # Username field
        username_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(LoginScreen)
        self.label.setFixedWidth(100)
        font = QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setText("Username:")
        username_layout.addWidget(self.label)
        
        self.te_username = QtWidgets.QLineEdit(LoginScreen)
        self.te_username.setFixedHeight(40)
        self.te_username.setPlaceholderText("Enter your username")
        username_layout.addWidget(self.te_username)
        layout.addLayout(username_layout)

        # Password field
        password_layout = QtWidgets.QHBoxLayout()
        self.label_2 = QtWidgets.QLabel(LoginScreen)
        self.label_2.setFixedWidth(100)
        font = QFont()
        font.setPointSize(12)
        self.label_2.setFont(font)
        self.label_2.setText("Password:")
        password_layout.addWidget(self.label_2)
        
        self.te_password = QtWidgets.QLineEdit(LoginScreen)
        self.te_password.setFixedHeight(40)
        self.te_password.setPlaceholderText("Enter your password")
        self.te_password.setEchoMode(QtWidgets.QLineEdit.Password)
        password_layout.addWidget(self.te_password)
        layout.addLayout(password_layout)

        # Add some spacing
        layout.addSpacing(20)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.btn_login = QtWidgets.QPushButton(LoginScreen)
        self.btn_login.setFixedHeight(40)
        self.btn_login.setText("Login")
        button_layout.addWidget(self.btn_login)
        
        self.btn_register = QtWidgets.QPushButton(LoginScreen)
        self.btn_register.setFixedHeight(40)
        self.btn_register.setText("Register")
        button_layout.addWidget(self.btn_register)
        
        layout.addLayout(button_layout)

        # Connect buttons
        self.btn_login.clicked.connect(self.login_request)
        self.btn_register.clicked.connect(self.register_request)

        # Add stretch to push everything up
        layout.addStretch()

        self.retranslateUi(LoginScreen)
        QtCore.QMetaObject.connectSlotsByName(LoginScreen)

    def retranslateUi(self, LoginScreen):
        LoginScreen.setWindowTitle(_translate("LoginScreen", "P2P Chat Application", None))

class LoginScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super(LoginScreen, self).__init__()
        self.ui = Ui_LoginScreen()
        self.ui.setupUi(self)
        self.mychannel = ServerChannel()
        self.ui.mychannel = self.mychannel
        self.setup_connections()
        
    def setup_connections(self):
        self.ui.btn_register.clicked.connect(self.ui.register_request)
        self.ui.btn_login.clicked.connect(self.ui.login_request)
        
    def closeEvent(self, event):
        if hasattr(self.ui, 'mychannel'):
            self.ui.mychannel.close()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_channel = ServerChannel('127.0.0.1', 3131, 5151)
    LOG.info("Channel connection started [ IP: {} , TCP PORT: {} , UDP PORT: {} ]".format('127.0.0.1', 3131, 5151))
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_LoginScreen(main_channel)
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
