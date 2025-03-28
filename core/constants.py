import logging
import os
import sys
import json

# File-based storage instead of MongoDB
DBPATH = 'users.json'
ONLINEUSERS = {}
CONECTIONS = []
TCP = 3131
UDP = 5151
ROOTPATH = ''
COLLECTIONS = "authentication"
DBNAME = "P2PApp"
TIMEOUT = 60

# Initialize users file if it doesn't exist
if not os.path.exists(DBPATH):
    with open(DBPATH, 'w') as f:
        json.dump({}, f)

for i in os.path.dirname(os.path.abspath(__file__)).split('/')[1:]:
    ROOTPATH = ROOTPATH+'/'+i
if ROOTPATH not in sys.path:
    sys.path.append(ROOTPATH)

def getlog():
    logFormatter = logging.Formatter(
        "%(asctime)s [%(filename)s  %(funcName)s  %(threadName)s ] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()

    if (len(rootLogger.handlers) > 0):
        return rootLogger
    rootLogger.setLevel(logging.INFO)
    fileHandler = logging.FileHandler('logfile.log')
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    return rootLogger