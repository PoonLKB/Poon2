import os
import sys

import wx
from ecmids import ECM_IDs
from pydispatch import dispatcher

from .base import HondaECU_AppPanel


class HondaECU_TunePanelHelper(HondaECU_AppPanel):

    def gen_model_tree(self):
        modeltree = {}
        for ecmid, info in ECM_IDs.items():
            if self.parent.force_restrictions and not info["model"] in self.parent.restrictions[1]:
                continue
            if not info["model"] in modeltree:
                modeltree[info["model"]] = {}
            if not info["year"] in modeltree[info["model"]]:
                modeltree[info["model"]][info["year"]] = {}
            if not info["pn"] in modeltree[info["model"]][info["year"]]:
                blcode = info["pn"].split("-")[1]
                modelstring = "%s_%s_%s" % (info["model"], blcode, info["year"])
                base = self.parent.basepath
                if not getattr(sys, 'frozen', False):
                    base = os.path.join(base, os.pardir)
                xdfdir = os.path.join(base, "xdfs", modelstring)
                bindir = os.path.join(base, "bins", modelstring)
                if os.path.exists(xdfdir) and os.path.exists(bindir):
                    xdf1 = os.path.join(xdfdir, "38770-%s.xdf" % (blcode))
                    xdf2 = os.path.join(xdfdir, "%s.xdf" % (info["pn"]))
                    bin = os.path.join(bindir, "%s.bin" % (info["pn"]))
                    checksum = info["checksum"] if "checksum" in info else None
                    offset = info["offset"] if "offset" in info else None
                    ecmidaddr = info["ecmidaddr"] if "ecmidaddr" in info else None
                    keihinaddr = info["keihinaddr"] if "keihinaddr" in info else None
                    if os.path.isfile(bin):
                        _xdf = None
                        if os.path.isfile(xdf2):
                            _xdf = xdf2
                        elif os.path.isfile(xdf1):
                            _xdf = xdf1
                        modeltree[info["model"]][info["year"]][info["pn"]] = (
                            ecmid, _xdf, bin, checksum, offset, ecmidaddr, keihinaddr)
        models = list(modeltree.keys())
        for m in models:
            years = list(modeltree[m].keys())
            for y in years:
                if len(modeltree[m][y].keys()) == 0:
                    del modeltree[m][y]
            if len(modeltree[m].keys()) == 0:
                del modeltree[m]
        return modeltree

    def Build(self):
        self.modeltree = self.gen_model_tree()
        self.outerp = wx.Panel(self)
        self.tunepickerp = wx.Panel(self.outerp)
        tunepickerpsizer = wx.GridBagSizer()
        self.tunepickerp.SetSizer(tunepickerpsizer)
        self.newrp = wx.RadioButton(self.tunepickerp, wx.ID_ANY, "", style=wx.RB_GROUP, name="new")
        self.Bind(wx.EVT_RADIOBUTTON, self.HandleRadioButtons, self.newrp)
        self.openrp = wx.RadioButton(self.tunepickerp, wx.ID_ANY, "", name="open")
        self.Bind(wx.EVT_RADIOBUTTON, self.HandleRadioButtons, self.openrp)
        self.newp = wx.Panel(self.tunepickerp)
        newpsizer = wx.StaticBoxSizer(wx.VERTICAL, self.newp, "Start a new tune")
        modelp = wx.Panel(self.newp)
        modelpsizer = wx.GridBagSizer()
        modell = wx.StaticText(modelp, wx.ID_ANY, label="Model")
        yearl = wx.StaticText(modelp, wx.ID_ANY, label="Year")
        ecul = wx.StaticText(modelp, wx.ID_ANY, label="ECU")
        self.racel = wx.StaticText(modelp, wx.ID_ANY, label="Restrictions")
        self.model = wx.ComboBox(modelp, wx.ID_ANY, size=(350, -1), choices=list(self.modeltree.keys()),
                                 style=wx.CB_READONLY | wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX, self.ModelHandler, self.model)
        self.year = wx.ComboBox(modelp, wx.ID_ANY, size=(350, -1), style=wx.CB_READONLY | wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX, self.YearHandler, self.year)
        self.year.Disable()
        self.ecu = wx.ComboBox(modelp, wx.ID_ANY, size=(350, -1), style=wx.CB_READONLY | wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX, self.ECUHandler, self.ecu)
        self.ecu.Disable()
        self.race = wx.ComboBox(modelp, wx.ID_ANY, size=(350, -1), style=wx.CB_READONLY | wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX, self.RaceHandler, self.race)
        self.race.Disable()
        modelpsizer.Add(modell, pos=(0, 0), flag=wx.ALIGN_RIGHT | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        modelpsizer.Add(yearl, pos=(1, 0), flag=wx.ALIGN_RIGHT | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        modelpsizer.Add(ecul, pos=(2, 0), flag=wx.ALIGN_RIGHT | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        modelpsizer.Add(self.racel, pos=(3, 0), flag=wx.ALIGN_RIGHT | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        modelpsizer.Add(self.model, pos=(0, 1), flag=wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        modelpsizer.Add(self.year, pos=(1, 1), flag=wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        modelpsizer.Add(self.ecu, pos=(2, 1), flag=wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        modelpsizer.Add(self.race, pos=(3, 1), flag=wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        modelp.SetSizer(modelpsizer)
        newpsizer.Add(modelp, 1, wx.EXPAND | wx.ALL, border=10)
        self.newp.SetSizer(newpsizer)
        self.openp = wx.Panel(self.tunepickerp)
        openpsizer = wx.StaticBoxSizer(wx.VERTICAL, self.openp, "Open an existing tune")
        self.openpicker = wx.FilePickerCtrl(self.openp, wildcard="HondaECU tune file (*.htf)|*.htf",
                                            style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL,
                                            size=(400, -1))
        openpsizer.Add(self.openpicker, 1, wx.EXPAND | wx.ALL, border=10)
        self.openp.SetSizer(openpsizer)
        self.continueb = wx.Button(self.tunepickerp, label="Continue")
        tunepickerpsizer.Add(self.newrp, pos=(0, 0),
                             flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        tunepickerpsizer.Add(self.openrp, pos=(1, 0),
                             flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        tunepickerpsizer.Add(self.newp, pos=(0, 1), flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                             border=0)
        tunepickerpsizer.Add(self.openp, pos=(1, 1),
                             flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        tunepickerpsizer.Add(self.continueb, pos=(2, 0), span=(1, 2),
                             flag=wx.ALIGN_RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)

        self.outersizer = wx.BoxSizer(wx.VERTICAL)
        self.outersizer.Add(self.tunepickerp, 1, wx.EXPAND | wx.ALL, border=10)
        self.outerp.SetSizer(self.outersizer)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.outerp, 1, wx.EXPAND)
        self.SetSizer(self.mainsizer)

        if self.parent.restrictions == None:
            self.race.Hide()
            self.racel.Hide()

        self.Layout()
        # self.mainsizer.Fit(self)
        self.continueb.Disable()
        self.openp.Disable()

        self.Bind(wx.EVT_BUTTON, self.OnContinue, self.continueb)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.ValidateContinueButton, self.openpicker)

    def OnContinue(self, event):
        if self.newrp.GetValue():
            ecupn = self.ecu.GetValue()
            model = self.model.GetValue()
            year = self.year.GetValue()
            r = self.race.GetValue()
            restrictions = None
            rid = None
            if r != "":
                if r in self.parent.restrictions[1][model] and self.parent.restrictions[0][r]:
                    restrictions = self.parent.restrictions[1][model][r]
                    rid = self.parent.restrictions[0][r]
            else:
                r = None
            _, xdf, bin, checksum, offset, ecmidaddr, keihinaddr = self.modeltree[model][year][ecupn]
            metainfo = {
                "model": model,
                "year": year,
                "ecupn": ecupn,
                "restriction": r,
                "rid": rid,
                "restrictions": restrictions,
                "checksum": checksum,
                "offset": offset,
                "ecmidaddr": ecmidaddr,
                "keihinaddr": keihinaddr,
            }
            dispatcher.send(signal="TunePanelHelper", sender=self, xdf=xdf, bin=bin, metainfo=metainfo, htf=None)
            wx.CallAfter(self.OnClose, None)
        elif self.openrp.GetValue():
            dispatcher.send(signal="TunePanelHelper", sender=self, xdf=None, bin=None, metainfo=None,
                            htf=self.openpicker.GetPath())
            wx.CallAfter(self.OnClose, None)

    def ValidateContinueButton(self, event):
        if self.newrp.GetValue():
            if self.ecu.GetValue() != "":
                if self.parent.force_restrictions and self.race.GetValue() == "":
                    self.continueb.Disable()
                    return
                self.continueb.Enable()
            else:
                self.continueb.Disable()
        elif self.openrp.GetValue():
            if os.path.isfile(self.openpicker.GetPath()):
                self.continueb.Enable()
            else:
                self.continueb.Disable()
        else:
            self.continueb.Disable()

    def HandleRadioButtons(self, event):
        if event.GetEventObject().GetName() == "open":
            self.openp.Enable()
            self.newp.Disable()
        elif event.GetEventObject().GetName() == "new":
            self.openp.Disable()
            self.newp.Enable()
        self.ValidateContinueButton(None)

    def ModelHandler(self, event):
        self.year.Clear()
        self.year.SetValue("")
        self.ecu.Clear()
        self.ecu.SetValue("")
        self.race.Clear()
        self.race.SetValue("")
        model = event.GetEventObject().GetValue()
        if self.parent.restrictions != None:
            if model in self.parent.restrictions[1]:
                for r in self.parent.restrictions[1][model]:
                    self.race.Append(r)
        years = self.modeltree[model].keys()
        if len(years) > 0:
            for y in years:
                self.year.Append(y)
            self.year.Enable()
            self.race.Enable()
        else:
            self.year.Disable()
            self.ecu.Disable()
            self.race.Disable()
        self.ValidateContinueButton(None)

    def YearHandler(self, event):
        self.ecu.Clear()
        self.ecu.SetValue("")
        ecus = self.modeltree[self.model.GetValue()][event.GetEventObject().GetValue()].keys()
        if len(ecus) > 0:
            for e in ecus:
                self.ecu.Append(e)
            self.ecu.Enable()
        else:
            self.ecu.Disable()
        self.ValidateContinueButton(None)

    def ECUHandler(self, event):
        self.ValidateContinueButton(None)

    def RaceHandler(self, event):
        self.ValidateContinueButton(None)
