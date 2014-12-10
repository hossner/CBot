import wx
import threading
import Queue

# --------------------- GUI Thread -------------------------

class GUIThread(threading.Thread):
    def __init__(self, serverConfig, Q2Main, Q2Sender):
        threading.Thread.__init__(self)

        self.serverConfig = serverConfig
        self.Q2Main = Q2Main
        self.Q2Sender = Q2Sender

        self.stop = False
        self.boundToGUI = False

        self.CBotServer = wx.App()

        # self.outputWidgets holds all widgets in the GUI that the server will want to update
        # 0=rawStreamOutput, 1=receivingStatusLabel 2=sendingStatusLabel
        self.outputWidgets = []

    def run(self):
        print self, ' GUI thread started'
        self.CBotGUI = CBotServerGUI(self.serverConfig, self)
        self.CBotServer.MainLoop()

        print self, ' GUI thread stopping'

    def cmdStop(self):
        wx.CallAfter(self.CBotGUI.Close)
        self.Q2Main.put('INT_STOP')
        None

    def displayMsg(self, theMsg):
        wx.CallAfter(self.CBotGUI.displayMsg, theMsg)

    # ============= Methods used by GUI =============
    def bindToGUI(self, widgets):
        self.outputWidgets = widgets
        self.boundToGUI = True


    def cmdToggleReceiverThread(self):
        self.CBotGUI.setStateReceiverThread(False)
        None

    def cmdToggleSenderThread(self):
        self.CBotGUI.setStateSenderThread(False)

    def cmdSendCmd(self, theCmd):
        print "  GUI Thread got: " + theCmd
        self.Q2Sender.put(theCmd)
    # ===============================================


class CBotServerGUI(wx.Frame):
    def __init__(self, serverConfig, guiThread):
        super(CBotServerGUI, self).__init__(None, title=serverConfig.appName, size=(971, 600))
        #self.bitmap
        self.guiThread = guiThread
        self.InitUI()
        self.Centre()
        self.Show()
        self.guiThread.bindToGUI([self.tcTelemetry, self.st1, self.st2])
        
    def InitUI(self):
    
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(11)

        panel = wx.Panel(self)

        box0 = wx.BoxSizer(wx.VERTICAL) # Two rows, top and bottom

        box1 = wx.BoxSizer(wx.HORIZONTAL)  # Three columns on top in box0
        box2 = wx.BoxSizer(wx.HORIZONTAL)  # Two columns on bottom in box0

        box1_1 = wx.BoxSizer(wx.VERTICAL)  # Five rows in box1
        box1_2 = wx.BoxSizer(wx.VERTICAL)  # Three rows in box1
        box1_3 = wx.BoxSizer(wx.VERTICAL)  # Two rows in box1

        box2_3 = wx.BoxSizer(wx.VERTICAL)  # Three rows in box2

        box1_1_1 = wx.BoxSizer(wx.HORIZONTAL)  # Two rows in box1_1
        box1_3_1 = wx.BoxSizer(wx.HORIZONTAL)  # Two rows in box1_3
        box1_3_3 = wx.BoxSizer(wx.HORIZONTAL)  # Two columns in box1_3

        box2_3_1 = wx.BoxSizer(wx.HORIZONTAL)  # Two rows in box2_3
        box2_3_2 = wx.BoxSizer(wx.VERTICAL)  # Five columns in box2_3

        box2_3_2_2 = wx.BoxSizer(wx.HORIZONTAL)

        self.st1 = wx.StaticText(panel, label='Not listening for telemetry')
        self.st1.SetFont(font)
        self.st2 = wx.StaticText(panel, label='No sending thread started')
        self.st2.SetFont(font)
        st3 = wx.StaticText(panel, label='RunMode: ')
        st3.SetFont(font)
        st4 = wx.StaticText(panel, label='Command: ')
        st4.SetFont(font)
        st5 = wx.StaticText(panel, label='Speed: ')
        st5.SetFont(font)
        st6 = wx.StaticText(panel, label='Volt: ')
        st6.SetFont(font)
        st7 = wx.StaticText(panel, label='CPU: ')
        st7.SetFont(font)
        st8 = wx.StaticText(panel, label='Telemetry stream')
        st8.SetFont(font)

        self.tcRunMode = wx.ComboBox(panel, -1, size=(80, -1), choices=['RM0', 'RM1', 'RM2', 'RM3', 'RM4', 'RM5'], style=wx.CB_READONLY)
        self.tcRunMode.SetSelection(3)

        self.tcCmd = wx.TextCtrl(panel)
        self.tcCmd.SetFocus()

        self.tcTelemetry = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        self.tcDummy = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        self.btnToggleReceiverThread = wx.Button(panel, label='Toggle listening', size=(100, 30))
        self.btnToggleReceiverThread.Bind(wx.EVT_BUTTON, self.OnBtnToggleReceiverThread)

        self.btnSendCmd = wx.Button(panel, label='Send', size=(70, 30))
        self.btnSendCmd.Bind(wx.EVT_BUTTON, self.OnBtnSendCmd)

        btnShowTelemetry = wx.Button(panel, label='Show stream', size=(100, 30))
        btnShowTelemetry.Bind(wx.EVT_BUTTON, self.OnBtnShowTelemetry)

        btnStopTelemetry = wx.Button(panel, label='Hide stream', size=(100, 30))
        btnStopTelemetry.Bind(wx.EVT_BUTTON, self.OnBtnHideTelemetry)

        btnFwd = wx.Button(panel, label='Fwd', size=(70, 30))
        btnFwd.Bind(wx.EVT_BUTTON, self.OnBtnFwd)

        btnStop = wx.Button(panel, label='Stop', size=(70, 30))
        btnStop.Bind(wx.EVT_BUTTON, self.OnBtnStop)

        btnBack = wx.Button(panel, label='Back', size=(70, 30))
        btnBack.Bind(wx.EVT_BUTTON, self.OnBtnBack)

        btnRight = wx.Button(panel, label='Right', size=(70, 30))
        btnRight.Bind(wx.EVT_BUTTON, self.OnBtnRight)

        btnLeft = wx.Button(panel, label='Left', size=(70, 30))
        btnLeft.Bind(wx.EVT_BUTTON, self.OnBtnLeft)

        btnExit = wx.Button(panel, label='Exit', size=(70, 30))
        btnExit.Bind(wx.EVT_BUTTON, self.OnBtnExit)

        box1_1_1.Add(st3, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        box1_1_1.Add(self.tcRunMode, proportion=1, flag=wx.EXPAND)

        box1_3_1.Add(st4, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        box1_3_1.Add(self.tcCmd, proportion=1, flag=wx.EXPAND)
        box1_3_1.Add(self.btnSendCmd, flag=wx.ALIGN_RIGHT)
        box1_3_1.Add(self.btnToggleReceiverThread, flag=wx.ALIGN_RIGHT)

        box1_1.Add(self.st1, flag=wx.ALIGN_LEFT, border=125)
        box1_1.Add(self.st2, flag=wx.ALIGN_LEFT, border=5)
        box1_1.Add(box1_1_1, 0, wx.TOP, 20)
        box1_1.Add(box1_3_1, flag=wx.EXPAND)

        box1_2.Add(st5, flag=wx.LEFT, border=5)
        box1_2.Add(st6, flag=wx.LEFT, border=5)
        box1_2.Add(st7, flag=wx.LEFT, border=5)
        
        box1_3.Add(st8, flag=wx.LEFT, border=5)
        box1_3.Add(self.tcTelemetry, 1, wx.EXPAND)

        box1_3_3.Add(btnShowTelemetry, flag=wx.ALIGN_CENTER_HORIZONTAL)
        box1_3_3.Add(btnStopTelemetry, flag=wx.ALIGN_CENTER_HORIZONTAL)
        box1_3.Add(box1_3_3)

        box2_3_2.Add(btnFwd, flag=wx.ALIGN_CENTER_HORIZONTAL)

        box2_3_2_2.Add(btnLeft)
        box2_3_2_2.Add(btnStop)
        box2_3_2_2.Add(btnRight)

        box2_3_2.Add(box2_3_2_2, flag=wx.ALIGN_CENTER_HORIZONTAL)

        box2_3_2.Add(btnBack, flag=wx.ALIGN_CENTER_HORIZONTAL)

        box2_3.Add(box2_3_1, 1, wx.ALIGN_CENTER_HORIZONTAL)
        box2_3.Add(box2_3_2, 1, wx.ALIGN_CENTER_HORIZONTAL)
        box2_3.Add(btnExit, flag=wx.ALIGN_RIGHT)

        box1.Add(box1_1, 1, wx.EXPAND)
        box1.Add(box1_2, 1, wx.EXPAND)
        box1.Add(box1_3, 1, wx.EXPAND)
        box2.Add(self.tcDummy, 1, wx.EXPAND)
        box2.Add(box2_3, 1, wx.EXPAND)

        box0.Add(box1, 0, wx.EXPAND|wx.ALL, 10)
        box0.Add(box2, 1, wx.EXPAND|wx.ALL, 10)

        panel.SetSizer(box0)

        print " GUI initialized"

# ================ Methods/signals tied to widgets =================

    def OnBtnToggleReceiverThread(self, evt):
        self.guiThread.cmdToggleReceiverThread()

    def OnBtnSendCmd(self, evt):
        if (self.tcCmd.GetLineLength(0) > 0):
            self.guiThread.cmdSendCmd(self.tcCmd.GetLineText(0))
        self.tcCmd.SetFocus()

    def OnBtnShowTelemetry(self, evt):
        self.rcvThread.toggleShowTelemetryStream(True)

    def OnBtnHideTelemetry(self, evt):
        self.rcvThread.toggleShowTelemetryStream(False)

    def OnBtnExit(self, evt):
        self.guiThread.cmdStop()
        #self.Close()

    def OnBtnStop(self, evt):
        self.guiThread.cmdSendCmd('MOV_HALT')

    def OnBtnFwd(self, evt):
        self.guiThread.cmdSendCmd('MOV_FWD')

    def OnBtnBack(self, evt):
        self.guiThread.cmdSendCmd('MOV_BACK')

    def OnBtnRight(self, evt):
        self.guiThread.cmdSendCmd('MOV_RIGHT')

    def OnBtnLeft(self, evt):
        self.guiThread.cmdSendCmd('MOV_LEFT')


# ============== Methods accessed and used by main thread ===============
    def displayMsg(self, theMsg):
        self.tcDummy.AppendText(theMsg+'\r\n')

    def setStateReceiverThread(self, isListening):
        if isListening:
            self.st1.SetLabel("Listening thread running")
            self.btnToggleReceiverThread.SetLabel("Stop receiving")
        else:
            self.st1.SetLabel("Listening thread not running!")
            self.btnToggleReceiverThread.SetLabel("Start receiving")

    def setStateSenderThread(self, isReady):
        if isReady:
            self.st2.SetLabel("Sending thread running")
            self.tcRunMode.Enabled = True
            self.btnSendCmd.Enabled = True
            self.tcCmd.Enabled = True
        else:
            self.st2.SetLabel("Sending thread not running!")
            self.tcRunMode.Enabled = False
            self.btnSendCmd.Enabled = False
            self.tcCmd.Enabled = False

