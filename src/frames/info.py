import wx
from ecmids import ECM_IDs
from eculib.honda import ECUSTATE

from .base import HondaECU_AppPanel


class HondaECU_InfoPanel(HondaECU_AppPanel):

    def Build(self):
        self.outerp = wx.Panel(self)
        self.infop = wx.Panel(self.outerp)
        infopsizer = wx.GridBagSizer(4, 2)
        ecmidl = wx.StaticText(self.infop, label="ECMID:")
        flashcountl = wx.StaticText(self.infop, label="Flash count:")
        modell = wx.StaticText(self.infop, label="Model:")
        ecul = wx.StaticText(self.infop, label="ECU P/N:")
        statel = wx.StaticText(self.infop, label="State:")
        ecmids = "unknown"
        models = "unknown"
        ecus = "unknown"
        flashcounts = "unknown"
        state = ECUSTATE.UNKNOWN

        self.ecmid = wx.StaticText(self.infop, label=ecmids)
        self.flashcount = wx.StaticText(self.infop, label=flashcounts)
        self.model = wx.StaticText(self.infop, label=models, size=(200, -1))
        self.ecu = wx.StaticText(self.infop, label=ecus)
        self.state = wx.StaticText(self.infop, label=str(state))
        infopsizer.Add(ecmidl, pos=(0, 0),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(modell, pos=(1, 0),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(ecul, pos=(2, 0),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(flashcountl, pos=(3, 0),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(statel, pos=(4, 0),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(self.ecmid, pos=(0, 1),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(self.model, pos=(1, 1),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(self.ecu, pos=(2, 1),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(self.flashcount, pos=(3, 1),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        infopsizer.Add(self.state, pos=(4, 1),
                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        self.infop.SetSizer(infopsizer)

        self.outersizer = wx.BoxSizer(wx.VERTICAL)
        self.outersizer.Add(self.infop, 1, wx.EXPAND | wx.ALL, border=10)
        self.outerp.SetSizer(self.outersizer)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.outerp, 1, wx.EXPAND)
        self.SetSizer(self.mainsizer)

        # self.mainsizer.Fit(self)
        self.Fit()
        self.Layout()

    def KlineWorkerHandler(self, info, value):
        if info == "ecmid":
            ecmid = "unknown"
            model = "unknown"
            ecu = "unknown"
            if len(value) > 0:
                ecmid = " ".join(["%02x" % i for i in value])
                if value in ECM_IDs:
                    model = "%s (%s)" % (ECM_IDs[value]["model"], ECM_IDs[value]["year"])
                    ecu = ECM_IDs[value]["pn"]
            self.ecmid.SetLabel(ecmid)
            self.model.SetLabel(model)
            self.ecu.SetLabel(ecu)
            self.Layout()
        elif info == "flashcount":
            if value >= 0:
                flashcount = str(value)
            else:
                flashcount = "unknown"
            self.flashcount.SetLabel(flashcount)
            self.Layout()
        elif info == "state":
            self.state.SetLabel(str(value))
            self.Layout()
