#!/usr/bin/python

import re
import sys
import netifaces as nifs
import CBotThreads
import Queue
import time
import threading

# ================ Misc variables ================
# CBOT_IP = "172.16.0.104"
SERVER_IP = "172.16.0.100"
CBOT_IP = "0"
SERVER_UDP_PORT = 5005
CBOT_TCP_PORT = 5006

configFileName = 'CBot.cfg'
RebootCBot = False
RunningCBot = False
queues = {}
threads = {}

# ================ Init queues ================
def initQueues():
    global queues
    queues = {
        "mainQueue": Queue.Queue(),
        "propulsionQueue": Queue.Queue(),
        "receiverQueue": Queue.Queue(),
        "senderQueue": Queue.Queue(),
        "telemetryQueue": Queue.Queue()
        }

# ================ Init threads ================
def initThreads():
    global threads
    threads = {
        "propulsionThread": CBotThreads.PropulsionThread(queues["mainQueue"], queues["propulsionQueue"]),
        "receiverThread": CBotThreads.ReceiverThread(queues["mainQueue"], queues["receiverQueue"], CBOT_IP, CBOT_TCP_PORT),
        "senderThread": CBotThreads.SenderThread(queues["mainQueue"], queues["senderQueue"], SERVER_IP, SERVER_UDP_PORT),
        "telemetryThread": CBotThreads.TelemetryThread(queues["mainQueue"], queues["telemetryQueue"], queues["senderQueue"])
        }

# ================ Methods ================
def getParameters(argv):
    global CBOT_IP
    global SERVER_IP
    if (len(argv) == 1):
        pat = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        if (pat.match(argv[0])):
            SERVER_IP = argv[0]
    try:
        CBOT_IP = nifs.ifaddresses('wlan0')[2][0]['addr']
    except:
        pass

def startThreads():
    for th in threads:
        try:
            threads[th].start()
        except:
            print 'Couldnt start thread ' + th
            stopThreads()
            sys.exit()

def stopThreads():
    for th in threads:
        if threads[th].isAlive():
            threads[th].cmdStop()

def handleQueue():
    startThreads()
    global RunningCBot
    while (RunningCBot):
        try:
            inp = queues["mainQueue"].get(True, 24*60*60) # Timeout set due to bug making it impossible to keyboard interrupt if not set
            cmd = inp.split('_', 1)
            if cmd[0] == 'CMD':
                try:
                    handleCommand(cmd[1])
                except:
                    queues["senderQueue"].put('ERR_PROCESSINGCMD_'+inp)
            elif cmd[0] == 'MOV':
                queues["propulsionQueue"].put(cmd[1])
            elif cmd[0] == 'ECHO':
                queues["senderQueue"].put(inp)
            else:
                queues["senderQueue"].put('ERR_UNKNOWNCMD_'+inp)
        except (KeyboardInterrupt, SystemExit):
            stopThreads()
            RunningCBot = False

# ================ Main methods ================

def handleCommand(cmd):
    print 'Handling command '+cmd
    subCmd1 = cmd.split('_', 1)
    global RebootCBot
    global RunningCBot
    if (subCmd1[0] == 'STOP') or (subCmd1[0] == 'RM0'):
        RebootCBot = False
        RunningCBot = False
        stopThreads()
    elif (subCmd1[0] == 'REBOOT'):
        RebootCBot = True
        RunningCBot = False
        stopThreads()
        time.sleep(5)
        initThreads()



if __name__ == "__main__":
    getParameters(sys.argv[1:])
    if CBOT_IP == "0":
        print "Unknown local IP..."
        sys.exit()
    initQueues()
    initThreads()
    RebootCBot = True
    while RebootCBot:
        RebootCBot = False
        RunningCBot = True
        handleQueue()


"""
def pinger(q2s):
    while True:
        q2s.put('ECHO_TIMEPING')
        time.sleep(2)

pingerThread = threading.Thread(pinger(senderQueue))
"""


'''

COMMANDS TO CBOT
CMD      Commands to CBot regarding it's internal operations and/or functions

    RCV  Commands to receiver thread
        STOP Shuts down the receiver thread (listening on TCP)

    SND  Commands to sender thread
        STOP Shuts down the sender thread (sending on UDP)

    TEL  Commands to telemetry thread
        STOP Shuts down the telemetry thread, including reading all telemetry

    PRO  Commands to propulsion thread
        STOP Shuts down the propulsion thread
        MOV_<cmd> Commands to direct the movement of the CBot.
            HALT  Halts CBot to a complete stop
            FWD   Moves CBot forward
            BACK  Moves CBot backward
            LEFT  Turns CBot left. Note that this means either turning (if moving either forward or backward) or swiveling (if standing still).
            RIGHT Turns CBot left. Note that this means either turning (if moving either forward or backward) or swiveling (if standing still).

    RUNM_<n> (where 0 <= n <= 6)  Changes to selected run mode. NOTE! NOT ALL RUN MODES ARE IMPLEMENTED!
          RM_0 equals "CMD_STOP"
          RM_5 equals "CMD_SLEEP"
          RM_6 equals "CMD_REBOOT"
    ECHO_<string>  Echoes <string>, prefixed with "ECHO_", back on UPD channel. String max len 30
    STOP  Shuts the CBot down to a not recoverable state. Equals run mode 0 (RM_0)
    SLEEP  Puts CBot in sleep mode. Equals run mode 5 (RM_5)
    REBOOT Reboots CBot; i.e. first shut downs and then restarts. Equals run mode 6 (RM_6)

MOV      Commands to manage movement to CBot. "MOV" can be seen as a shortcut for "CMD_PRO_MOV"

Internal prefixes:
ERR_
INT_


COMMANDS TO CBOTSERVER
ERR_<string>  Signals an error, specified by <string>
INF_<string>  Signals information, specified by <string>
ECHO_<string>  Responds to a ECHO_<string> request by CBotServer
n:<telemetry>  (Where n is the id of the sensor) Signals telemetry



SPLIT----------------------------------------------
Example

The following example shows the usage of split() method.

#!/usr/bin/python

str = "Line1-abcdef \nLine2-abc \nLine4-abcd";
print str.split( );
print str.split(' ', 1 );

Let us compile and run the above program, this will produce the following result:

['Line1-abcdef', 'Line2-abc', 'Line4-abcd']
['Line1-abcdef', '\nLine2-abc \nLine4-abcd']


SPLICE----------------------------------------------
a[start:end] # items start through end-1
a[start:]    # items start through the rest of the array
a[:end]      # items from the beginning through end-1
a[:]         # a copy of the whole array

There is also the step value, which can be used with any of the above:

a[start:end:step] # start through not past end, by step

The key point to remember is that the :end value represents the first value that is not in the selected slice. So, the difference beween end and start is the number of elements selected (if step is 1, the default).

The other feature is that start or end may be a negative number, which means it counts from the end of the array instead of the beginning. So:

a[-1]    # last item in the array
a[-2:]   # last two items in the array
a[:-2]   # everything except the last two items
'''

