import ConfigParser
import socket

class ServerConfig():
    def __init__(self, filename):
        self.filename = filename
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.filename)
        self.appName = 'CBot Server v 0.2'
        self.serverIP = self.config.get('NETWORK', 'SERVER_IP')
        self.cbotIP = self.config.get('NETWORK', 'CBOT_IP')
        self.udpPort = self.config.getint('NETWORK', 'UDP_PORT')
        self.tcpPort = self.config.getint('NETWORK', 'TCP_PORT')
        self.bufferSize = self.config.getint('NETWORK', 'BUFFER_SIZE')
        self.headless = self.config.getboolean('GUI', 'RUN_HEADLESS')
