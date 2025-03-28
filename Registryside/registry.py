from socket import *
import signal
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Registryside.conlistener import Listener
from Registryside.UdpListener import ListenerUdp
from Registryside.inspector import Checker
from core.constants import getlog,TCP,UDP,CONECTIONS

LOG=getlog()
udpthread=None
checkerthread=None
serverSocket=None

def cleanup():
    global serverSocket, udpthread, checkerthread
    if serverSocket:
        try:
            serverSocket.close()
        except:
            pass
    if udpthread:
        udpthread._stop()
    if checkerthread:
        checkerthread.stop()
    sys.exit(0)

def signal_handler(sig, frame):
    LOG.info("Shutting down server...")
    cleanup()

signal.signal(signal.SIGINT, signal_handler)

def initalize():
    global checkerthread, udpthread, serverSocket
    try:
        udpthread=ListenerUdp(port=UDP)
        udpthread.start()
        checkerthread = Checker()
        checkerthread.start()
        listentPeers()
    except Exception as e:
        LOG.error(f"Failed to initialize server: {str(e)}")
        cleanup()

def listentPeers():
    global serverSocket
    try:
        serverSocket = socket(AF_INET, SOCK_STREAM)
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(('', TCP))
        serverSocket.listen(1)
        LOG.info("Server is listing on tcp    [ 0.0.0.0 , {} ]".format(TCP))

        while True:
            connectionSocket, addr = serverSocket.accept()
            LOG.info("Connection accepted from    [ {} , {} ]".format(addr[0],addr[1]))
            thread = Listener(host=addr, socket=connectionSocket)
            thread.start()
            CONECTIONS.append(thread)
    except Exception as e:
        LOG.error(f"Error in server: {str(e)}")
        cleanup()

if __name__ == "__main__":
    try:
        initalize()
    except KeyboardInterrupt:
        cleanup()