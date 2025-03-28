from socket import *
import struct
import threading
import time
from core.constants import getlog


class ServerChannel():
    def __init__(self, ip, portTcp, portUDp):
        self.ip = ip
        self.portTcp = portTcp
        self.portUdp = portUDp
        self.sock = None
        self.log = getlog()
        self.username = ''
        self.password = ''
        self.udpThread = threading.Thread(target=self.sendHello)
        self.connected = False

    def connect(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((self.ip, self.portTcp))
            self.connected = True
            self.log.info(f"Connection Established with Registry [{self.ip}, {self.portTcp}]")
            return True
        except Exception as e:
            self.log.error(f"Connection failed to Registry [{self.ip}, {self.portTcp}]: {str(e)}")
            self.connected = False
            return False

    def closeChannel(self):
        if self.sock:
            self.sock.close()
            self.connected = False

    def purge(self, message):
        message = message.decode('utf-8')
        index = message.find('\x00')
        if index != -1:
            return message[0:index]
        return message

    def operations(self, which, username='', password='', search_name=''):
        if not self.connected:
            self.log.error("Not connected to server")
            return [-1, "Not connected"]

        try:
            packet = None

            if which == 0:  # register
                packet = struct.pack('b 10s 15s b', 0, bytes(username, 'utf-8'), bytes(password, 'utf-8'), 15)
            elif which == 1:  # login
                packet = struct.pack('b 10s 15s b', 1, bytes(username, 'utf-8'), bytes(password, 'utf-8'), 15)
            elif which == 2:  # search
                packet = struct.pack('b 10s 15s b', 2, bytes(self.username, 'utf-8'), bytes(search_name, 'utf-8'), 15)
            elif which == 3:  # logout
                packet = struct.pack('b 10s 15s b', 3, bytes(self.username, 'utf-8'), bytes('LOGOUT', 'utf-8'), 15)
            elif which == 4:  # all online
                packet = struct.pack('b 10s 15s b', 4, bytes(self.username, 'utf-8'), bytes('All', 'utf-8'), 15)

            if not packet:
                return [-1, "Invalid operation"]

            self.sock.send(packet)
            received_packet = self.sock.recv(1024)

            if not received_packet:
                return [-1, "No response from server"]

            typ, code, message, key = struct.unpack('b b 15s b', received_packet[0:18])
            message = self.purge(message)
            
            if typ == 4 or code == 24:
                self.log.info("Online users acknowledgment")
                online_data = received_packet[18:]
                return [code, message, online_data]

            self.log.info(f"Response {typ} {code} {message} {key}")
            return [code, message]

        except Exception as e:
            self.log.error(f"Operation error: {str(e)}")
            return [-1, str(e)]

    def online_users(self, packet):
        data = str(packet, 'utf-8')
        pure_data = data.split(" /t/n")[:-1]
        return pure_data

    def sendHello(self):
        while self.connected:
            try:
                serverUdp = socket(AF_INET, SOCK_DGRAM)
                packet = struct.pack('b 10s 10s b', 5, bytes(self.username, 'utf-8'), bytes("HELLO", 'utf-8'), 15)
                for _ in range(2):
                    serverUdp.sendto(packet, (self.ip, self.portUdp))
                time.sleep(1)
            except Exception as e:
                self.log.error(f"Hello message error: {str(e)}")
                break

    def send_request(self, type, field1, field2, field3):
        try:
            if not self.connected and not self.connect():
                return [-1, "Failed to connect to server"]

            result = self.operations(which=type, username=field1, password=field2, search_name=field3)
            self.username = field1

            if result[0] == 21:  # successful login
                if not hasattr(self, 'udpThread') or not self.udpThread.is_alive():
                    self.udpThread = threading.Thread(target=self.udp_broadcast)
                    self.udpThread.daemon = True
                    self.udpThread.start()
            return result
        except Exception as e:
            self.log.error(f"Request error: {str(e)}")
            return [-1, str(e)]

    def udp_broadcast(self):
        while self.connected:
            try:
                serverUdp = socket(AF_INET, SOCK_DGRAM)
                packet = struct.pack('b 10s 10s b', 5, bytes(self.username, 'utf-8'), bytes("HELLO", 'utf-8'), 15)
                for _ in range(2):
                    serverUdp.sendto(packet, (self.ip, self.portUdp))
                time.sleep(1)
            except Exception as e:
                self.log.error(f"Hello message error: {str(e)}")
                break

