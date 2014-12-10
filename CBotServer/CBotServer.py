#!/usr/bin/python

import wx
import CBotServerCfg
import CBotServerGUI
import CBotServerThreads
import time
import Queue

# ====== Constants =======
CONFIG_FILE_NAME = "CBotServer.cfg"

serverCfg = CBotServerCfg.ServerConfig(CONFIG_FILE_NAME)

# ====== Queues =======
queues = {
    "mainQueue": Queue.Queue(),
    "receiverQueue": Queue.Queue(),
    "senderQueue": Queue.Queue(),
    "aiQueue": Queue.Queue(),
}

# ====== Threads =======
threads = {
    "guiThread": None,
    "receiverThread": CBotServerThreads.ReceiverThread(serverCfg, queues["mainQueue"], queues["receiverQueue"], queues["aiQueue"]),
    "senderThread": CBotServerThreads.SenderThread(serverCfg, queues["mainQueue"], queues["senderQueue"]),
    "aiThread": CBotServerThreads.AIThread(serverCfg, queues["mainQueue"], queues["aiQueue"], queues["senderQueue"]),
}

def startThreads():
    for th in threads:
        if (th != "guiThread") or (not serverCfg.headless):
            threads[th].start()

def stopGUIThread():
    if (threads["guiThread"] != None) and (threads["guiThread"].isAlive()):
        threads["guiThread"].cmdStop()

def stopAllThreads():
    for th in threads:
        if (threads[th] != None) and (threads[th].isAlive()):
            threads[th].cmdStop()

if (not serverCfg.headless):
    print "Server running with GUI"
    threads["guiThread"] = CBotServerGUI.GUIThread(serverCfg, queues["mainQueue"], queues["senderQueue"])
else:
    print "Server running headless mode"
startThreads()

while (True):
    try:
        QCmd = queues["mainQueue"].get()
        cmd = QCmd.split('_')
        if (cmd[0] == 'INT'):        # Internal commands to main or other threads
            if (cmd[1] == 'STOP'):
                stopAllThreads()
                break
            elif (cmd[1] == 'MSG'):  # Message from internal thread
                None
                # The message to be printed or shown in GUI
            else:
                break
        elif (cmd[0] == 'ERR') or (cmd[0] == 'INF') or (cmd[0] == 'ECHO'):  # Should be from CBot...
            if (serverCfg.headless):
                print "From CBot: " + cmd[1]
            else:
                threads["guiThread"].displayMsg("From CBot: " + cmd[1])
            None
            # Display the echoed message on console or GUI
    except (KeyboardInterrupt, SystemExit):
        stopAllThreads()
        raise KeyboardInterrupt
        break



"""
Commands to server (through UDP)

ERR

ACK

ECHO

"""
