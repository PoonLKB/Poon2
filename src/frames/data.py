import wx
from eculib.honda import *

from .base import HondaECU_AppPanel


def changeFontInChildren(win, font):
    try:
        win.SetFont(font)
    except:
        pass
    for child in win.GetChildren():
        changeFontInChildren(child, font)


class HondaECU_DatalogPanel(HondaECU_AppPanel):

    def __init__(self, parent, appid, appinfo, enablestates, *args, **kwargs):
        wx.Panel.__init__(self, parent.labelbook, size=(820, -1), *args, **kwargs)
        self.parent = parent
        self.appid = appid
        self.appinfo = appinfo
        self.enablestates = enablestates
        self.Build()
        dispatcher.connect(self.KlineWorkerHandler, signal="KlineWorker", sender=dispatcher.Any)
        dispatcher.connect(self.DeviceHandler, signal="FTDIDevice", sender=dispatcher.Any)

    def prepare_data1(self, data, t):
        if t in [0x13, 0x17]:
            data = data[:9] + [0xff, 0xff] + data[9:]
        data[1] = round(data[1] / 0xff * 5.0, 2)
        data[2] = round(data[2] / 1.6, 2)
        data[3] = round(data[3] / 0xff * 5.0, 2)
        data[4] = -40 + data[4]
        data[5] = round(data[5] / 0xff * 5.0, 2)
        data[6] = -40 + data[6]
        data[7] = round(data[7] / 0xff * 5.0, 2)
        data[8] = 10 * data[8]
        data[11] = round(data[11] / 10, 2)
        data[13] = round(data[13] / 0xffff * 265.5, 2)
        data[14] = round(-64 + data[14] / 0xff * 127.5, 2)
        if t in [0x11]:
            data[16] = round(data[16] / 0xffff * 8.0, 4)
        return data

    def clear_tables(self):
        for i, l in enumerate(self.sensors.keys()):
            self.sensors[l][1].SetLabel("---")
        for i, l in enumerate(self.sensors2.keys()):
            self.sensors2[l][1].SetLabel("---")
        for j in self.o2sensor:
            for i, l in enumerate(self.o2sensor[j].keys()):
                self.o2sensor[j][l][1].SetLabel("---")

    def Build(self):
        self.datap = wx.Panel(self)

        self.d1pbox = wx.Panel(self)
        self.d1p = wx.Panel(self.d1pbox)
        self.d1psizer = wx.GridBagSizer()

        self.d2pbox = wx.Panel(self)
        self.d2p = wx.Panel(self.d2pbox)
        self.d2psizer = wx.GridBagSizer()

        self.d3pbox = wx.Panel(self)
        self.d3p = wx.Panel(self.d3pbox)
        self.d3psizer = wx.GridBagSizer()

        self.d4pbox = wx.Panel(self)
        self.d4p = wx.Panel(self.d4pbox)
        self.d4psizer = wx.GridBagSizer()

        self.maintable = None
        self.sensors = {
            "Engine speed": [None, None, None, "rpm", 0, True, self.d1psizer, self.d1p],
            "TPS sensor": [None, None, None, "%", 2, True, self.d1psizer, self.d1p],
            "ECT sensor": [None, None, None, "°C", 4, True, self.d1psizer, self.d1p],
            "IAT sensor": [None, None, None, "°C", 6, True, self.d1psizer, self.d1p],
            "MAP sensor": [None, None, None, "mBar", 8, True, self.d1psizer, self.d1p],
            "Battery voltage": [None, None, None, "V", 11, True, self.d1psizer, self.d1p],
            "Vehicle speed": [None, None, None, "Km/h", 12, True, self.d1psizer, self.d1p],
            "Injector duration": [None, None, None, "ms", 13, True, self.d1psizer, self.d1p],
            "Ignition advance": [None, None, None, "°", 14, True, self.d1psizer, self.d1p],
            "IACV pulse count": [None, None, None, "", 15, True, self.d1psizer, self.d1p],
            "IACV command": [None, None, None, "", 16, True, self.d1psizer, self.d1p]
        }
        self.o2sensor = {
            0x20: {
                "O2 sensor #1": [None, None, None, "V", 0, True, self.d2psizer, self.d2p, self.d2pbox],
                "O2 heater #1": [None, None, None, "V", 2, True, self.d2psizer, self.d2p, self.d2pbox],
                "STFT #1": [None, None, None, "", 1, True, self.d2psizer, self.d2p, self.d2pbox]
            },
            0x21: {
                "O2 sensor #2": [None, None, None, "V", 0, True, self.d3psizer, self.d3p, self.d3pbox],
                "O2 heater #2": [None, None, None, "V", 2, True, self.d3psizer, self.d3p, self.d3pbox],
                "STFT #2": [None, None, None, "", 1, True, self.d3psizer, self.d3p, self.d3pbox]
            },
        }
        self.sensors2 = {
            "EGCV current": [None, None, None, "V", 5, True, self.d4psizer, self.d4p, self.d4pbox],
            "EGCV target": [None, None, None, "V", 6, True, self.d4psizer, self.d4p, self.d4pbox],
            "EGCV load": [None, None, None, "%", 7, True, self.d4psizer, self.d4p, self.d4pbox],
            "HESD current": [None, None, None, "A", 8, True, self.d4psizer, self.d4p, self.d4pbox],
            "HESD target": [None, None, None, "A", 9, True, self.d4psizer, self.d4p, self.d4pbox],
            "HESD load": [None, None, None, "%", 10, True, self.d4psizer, self.d4p, self.d4pbox]
        }
        for i, l in enumerate(self.sensors.keys()):
            self.sensors[l][0] = wx.StaticText(self.sensors[l][7], label="%s:" % l)
            self.sensors[l][1] = wx.StaticText(self.sensors[l][7], label="---")
            self.sensors[l][2] = wx.StaticText(self.sensors[l][7], label=self.sensors[l][3])
            self.sensors[l][6].Add(wx.StaticText(self.sensors[l][7], label=" "), pos=(i, 0))
            self.sensors[l][6].Add(self.sensors[l][0], pos=(i, 1),
                                   flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
            self.sensors[l][6].Add(wx.StaticText(self.sensors[l][7], label=" "), pos=(i, 2))
            self.sensors[l][6].Add(self.sensors[l][1], pos=(i, 3),
                                   flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
            self.sensors[l][6].Add(self.sensors[l][2], pos=(i, 4),
                                   flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, border=5)
            self.sensors[l][6].Add(wx.StaticText(self.sensors[l][7], label=" "), pos=(i, 5))
        for i, l in enumerate(self.sensors2.keys()):
            self.sensors2[l][0] = wx.StaticText(self.sensors2[l][7], label="%s:" % l)
            self.sensors2[l][1] = wx.StaticText(self.sensors2[l][7], label="---")
            self.sensors2[l][2] = wx.StaticText(self.sensors2[l][7], label=self.sensors2[l][3])
            self.sensors2[l][6].Add(wx.StaticText(self.sensors2[l][7], label=" "), pos=(i, 0))
            self.sensors2[l][6].Add(self.sensors2[l][0], pos=(i, 1),
                                    flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
            self.sensors2[l][6].Add(wx.StaticText(self.sensors2[l][7], label=" "), pos=(i, 2))
            self.sensors2[l][6].Add(self.sensors2[l][1], pos=(i, 3),
                                    flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
            self.sensors2[l][6].Add(self.sensors2[l][2], pos=(i, 4),
                                    flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, border=5)
            self.sensors2[l][6].Add(wx.StaticText(self.sensors2[l][7], label=" "), pos=(i, 5))
        for j in self.o2sensor:
            for i, l in enumerate(self.o2sensor[j].keys()):
                self.o2sensor[j][l][0] = wx.StaticText(self.o2sensor[j][l][7], label="%s:" % l)
                self.o2sensor[j][l][1] = wx.StaticText(self.o2sensor[j][l][7], label="---")
                self.o2sensor[j][l][2] = wx.StaticText(self.o2sensor[j][l][7], label=self.o2sensor[j][l][3])
                self.o2sensor[j][l][6].Add(wx.StaticText(self.o2sensor[j][l][7], label=" "), pos=(i, 0))
                self.o2sensor[j][l][6].Add(self.o2sensor[j][l][0], pos=(i, 1),
                                           flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
                self.o2sensor[j][l][6].Add(wx.StaticText(self.o2sensor[j][l][7], label=" "), pos=(i, 2))
                self.o2sensor[j][l][6].Add(self.o2sensor[j][l][1], pos=(i, 3),
                                           flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, border=5)
                self.o2sensor[j][l][6].Add(self.o2sensor[j][l][2], pos=(i, 4),
                                           flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.ALL, border=5)
                self.o2sensor[j][l][6].Add(wx.StaticText(self.o2sensor[j][l][7], label=" "), pos=(i, 5))

        self.d1p.SetSizer(self.d1psizer)
        self.d2p.SetSizer(self.d2psizer)
        self.d3p.SetSizer(self.d3psizer)
        self.d4p.SetSizer(self.d4psizer)

        self.d1pboxsizer = wx.StaticBoxSizer(wx.VERTICAL, self.d1pbox, "Table 0x??")
        self.d1pboxsizer.Add(self.d1p, 0, wx.ALL, border=10)
        self.d1pbox.SetSizer(self.d1pboxsizer)

        self.d2pboxsizer = wx.StaticBoxSizer(wx.VERTICAL, self.d2pbox, "Table 0x20")
        self.d2pboxsizer.Add(self.d2p, 0, wx.ALL, border=10)
        self.d2pbox.SetSizer(self.d2pboxsizer)

        self.d3pboxsizer = wx.StaticBoxSizer(wx.VERTICAL, self.d3pbox, "Table 0x21")
        self.d3pboxsizer.Add(self.d3p, 0, wx.ALL, border=10)
        self.d3pbox.SetSizer(self.d3pboxsizer)

        self.d4pboxsizer = wx.StaticBoxSizer(wx.VERTICAL, self.d4pbox, "Table 0xd0")
        self.d4pboxsizer.Add(self.d4p, 0, wx.ALL, border=10)
        self.d4pbox.SetSizer(self.d4pboxsizer)

        self.datapsizer = wx.GridBagSizer()
        self.datapsizer.Add(self.d1pbox, pos=(0, 0), span=(3, 1), flag=wx.ALL | wx.EXPAND, border=10)
        self.datapsizer.Add(self.d2pbox, pos=(0, 1), span=(1, 1), flag=wx.ALL | wx.EXPAND, border=10)
        self.datapsizer.Add(self.d3pbox, pos=(1, 1), span=(1, 1), flag=wx.ALL | wx.EXPAND, border=10)
        self.datapsizer.Add(self.d4pbox, pos=(0, 2), span=(2, 1), flag=wx.ALL | wx.EXPAND, border=10)

        self.datap.SetSizer(self.datapsizer)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.datap, 1, wx.EXPAND)

        self.d2pbox.Disable()
        self.d3pbox.Disable()
        self.d4pbox.Disable()

        self.SetSizer(self.mainsizer)
        self.Fit()
        self.Layout()
        # self.mainsizer.Fit(self)

        wx.CallAfter(dispatcher.send, signal="DatalogPanel", sender=self, action="data.on")

        self.font1 = self.GetFont()
        self.font2 = self.GetFont().Bold()
        self.font2.SetPointSize(self.font1.GetPointSize() * 1.25)
        self.font3 = self.GetFont().Bold()
        self.font3.SetPointSize(self.font1.GetPointSize() * 1.5)
        self.font4 = self.GetFont().Bold()
        self.font4.SetPointSize(self.font1.GetPointSize() * 1.75)
        self.font5 = self.GetFont().Bold()
        self.font5.SetPointSize(self.font1.GetPointSize() * 2)
        self.fonts = {
            wx.NewId(): [self.font1, 5 * 1],
            wx.NewId(): [self.font2, 5 * 1.5],
            wx.NewId(): [self.font3, 5 * 2],
            wx.NewId(): [self.font4, 5 * 2.5],
            wx.NewId(): [self.font5, 5 * 3],
        }
        for s in [self.d1psizer, self.d2psizer, self.d3psizer, self.d4psizer]:
            s.SetHGap(5)

        at = []
        for i, iid in enumerate(self.fonts):
            self.Bind(wx.EVT_MENU, self.OnBig, id=iid)
            at.append((wx.ACCEL_CTRL, ord('%s' % (i + 1)), iid))
        accel_tbl = wx.AcceleratorTable(at)
        self.SetAcceleratorTable(accel_tbl)

    def OnBig(self, event):
        f = self.fonts[event.GetId()]
        changeFontInChildren(self, f[0])
        for s in [self.d1psizer, self.d2psizer, self.d3psizer, self.d4psizer]:
            s.SetHGap(f[1])
        self.Layout()

    def OnClose(self, event):
        wx.CallAfter(dispatcher.send, signal="DatalogPanel", sender=self, action="data.off")
        HondaECU_AppPanel.OnClose(self, event)

    def KlineWorkerHandler(self, info, value):
        if info == "data":
            t = value[0]
            d = value[2][2:]
            if t in [0x10, 0x11, 0x13, 0x17]:
                u = ">H12B"
                if t is not 0x13:
                    u += "HB"
                    if t == 0x11:
                        u += "BH"
                    elif t == 0x17:
                        u += "BB"
                data = self.prepare_data1(list(struct.unpack(u, d)), t)
                ld = len(data)
                for s in self.sensors:
                    if self.sensors[s][4] < ld:
                        if self.sensors[s][5]:
                            self.sensors[s][1].SetLabel(str(data[self.sensors[s][4]]))
                if self.maintable is None:
                    if t not in [0x11]:
                        for s in ["IACV pulse count", "IACV command"]:
                            self.sensors[s][0].Hide()
                            self.sensors[s][1].Hide()
                            self.sensors[s][2].Hide()
                            self.sensors[s][5] = False
                            self.Layout()
                        # self.mainsizer.Fit(self)
                    self.maintable = t
                    mt = "0x%x" % self.maintable
                    self.d1pboxsizer.GetStaticBox().SetLabel("Table " + mt)
            if t in [0x20, 0x21]:
                data = list(struct.unpack(">3B", d))
                data[0] = round(data[0] / 0xff * 5, 2)
                data[1] = round(data[1] / 0xff * 2, 4)
                data[2] = round(data[2] / 0xff * 5, 2)
                for s in self.o2sensor[t]:
                    if self.o2sensor[t][s][5]:
                        self.o2sensor[t][s][1].SetLabel(str(data[self.o2sensor[t][s][4]]))
                        self.o2sensor[t][s][8].Enable()
                        self.Layout()
                    # self.mainsizer.Fit(self)
            if t == 0xd0:
                data = list(struct.unpack(">7Bb%dB" % (value[1] - 10), d))
                data[5] = round(data[5] / 0xff * 5, 3)
                data[6] = round(data[6] / 0xff * 5, 3)
                # data[7] = round(data[7]/0xff*5, 2)
                data[8] = round(data[8] / 0xff * 5, 3)
                data[9] = round(data[9] / 0xff * 5, 3)
                # data[10] = round(data[10]/0xff*5, 2)
                for s in self.sensors2:
                    if self.sensors2[s][5]:
                        self.sensors2[s][1].SetLabel(str(data[self.sensors2[s][4]]))
                        self.sensors2[s][8].Enable()
                        self.Layout()
                    # self.mainsizer.Fit(self)

        elif info == "state":
            if value == ECUSTATE.OK:
                wx.CallAfter(dispatcher.send, signal="DatalogPanel", sender=self, action="data.on")
            else:
                wx.CallAfter(dispatcher.send, signal="DatalogPanel", sender=self, action="data.off")
                self.clear_tables()
                self.maintable = None
                self.d1pboxsizer.GetStaticBox().SetLabel("Table 0x??")
            self.Layout()
        # self.mainsizer.Fit(self)

    def DeviceHandler(self, action, device, config):
        if action == "deactivate":
            for s in self.sensors:
                if self.sensors[s][5]:
                    self.sensors[s][1].SetLabel("---")
            self.d1pboxsizer.GetStaticBox().SetLabel("Table 0x??")
            self.Layout()
        # self.mainsizer.Fit(self)
