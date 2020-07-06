import os

import wx
from eculib.honda import *

from .base import HondaECU_AppPanel


class HondaECU_EEPROMPanel(HondaECU_AppPanel):

    def Build(self):
        self.wildcard = "EEPROM dump (*.bin)|*.bin"
        self.byts = None
        self.mainp = wx.Panel(self)

        self.formatbox = wx.RadioBox(self.mainp, label="Fill byte", choices=["0x00", "0xFF"])

        self.wfilel = wx.StaticText(self.mainp, label="File")
        self.fpickerbox = wx.BoxSizer(wx.HORIZONTAL)
        self.fpickerbox.Add(self.wfilel, 1)
        self.fpickerbox.Add(self.formatbox, 0)

        self.readfpicker = wx.FilePickerCtrl(self.mainp, wildcard=self.wildcard,
                                             style=wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL)
        self.writefpicker = wx.FilePickerCtrl(self.mainp, wildcard=self.wildcard,
                                              style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL)

        self.progressboxp = wx.Panel(self.mainp)
        self.progressbox = wx.BoxSizer(wx.VERTICAL)
        self.lastpulse = time.time()
        self.progress = wx.Gauge(self.progressboxp, style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        self.progress.SetRange(100)
        self.progressboxp.Hide()
        self.progress_text = wx.StaticText(self.progressboxp, size=(32, -1), style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.progressbox.Add(self.progress, 1, flag=wx.EXPAND)
        self.progressbox.Add(self.progress_text, 0, flag=wx.EXPAND | wx.TOP, border=10)
        self.progressboxp.SetSizer(self.progressbox)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.mainp, 1, wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(self.mainsizer)

        self.gobutton = wx.Button(self.mainp, label="Read")
        self.gobutton.Disable()

        self.fpickerbox = wx.BoxSizer(wx.HORIZONTAL)
        self.fpickerbox.AddSpacer(5)
        self.fpickerbox.Add(self.readfpicker, 1)
        self.fpickerbox.Add(self.writefpicker, 1)

        self.modebox = wx.RadioBox(self.mainp, label="Mode", choices=["Read", "Write", "Format"])

        self.eeprompsizer = wx.GridBagSizer()
        self.eeprompsizer.Add(self.wfilel, pos=(0, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
                              border=10)
        self.eeprompsizer.Add(self.fpickerbox, pos=(0, 1), span=(1, 5), flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM,
                              border=10)
        self.eeprompsizer.Add(self.progressboxp, pos=(3, 0), span=(1, 6),
                              flag=wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND | wx.TOP, border=20)
        self.eeprompsizer.Add(self.modebox, pos=(4, 0), span=(1, 2), flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.LEFT | wx.TOP,
                              border=30)
        self.eeprompsizer.Add(self.gobutton, pos=(5, 5), flag=wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.RIGHT, border=10)
        self.eeprompsizer.AddGrowableRow(2, 1)
        self.eeprompsizer.AddGrowableCol(5, 1)
        self.mainp.SetSizer(self.eeprompsizer)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.mainp, 1, wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(self.mainsizer)

        self.readfpicker.Hide()
        self.formatbox.Hide()

        self.Fit()
        self.Layout()

        self.OnModeChange(None)

        self.readfpicker.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnReadPicker)
        self.writefpicker.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnWritePicker)
        self.modebox.Bind(wx.EVT_RADIOBOX, self.OnModeChange)
        self.gobutton.Bind(wx.EVT_BUTTON, self.OnGo)

    def OnGo(self, _event):
        self.gobutton.Disable()
        if self.modebox.GetSelection() == 0:
            dispatcher.send(signal="eeprom", sender=self, cmd="read", data=self.readfpicker.GetPath())
        elif self.modebox.GetSelection() == 1:
            dispatcher.send(signal="eeprom", sender=self, cmd="write", data=self.byts)
        elif self.modebox.GetSelection() == 2:
            dispatcher.send(signal="eeprom", sender=self, cmd="format", data=self.formatbox.GetSelection())

    def OnReadPicker(self, _event):
        self.OnValidateMode(None)

    def OnWritePicker(self, _event):
        self.OnValidateMode(None)

    def OnValidateMode(self, _event):
        enable = False
        if "state" in self.parent.ecuinfo:
            if self.parent.ecuinfo["state"] == ECUSTATE.SECURE:
                if self.modebox.GetSelection() == 0:
                    enable = len(self.readfpicker.GetPath()) > 0
                elif self.modebox.GetSelection() == 1:
                    if len(self.writefpicker.GetPath()) > 0:
                        if os.path.isfile(self.writefpicker.GetPath()):
                            fbin = open(self.writefpicker.GetPath(), "rb")
                            nbyts = os.path.getsize(self.writefpicker.GetPath())
                            if nbyts in [256, 512]:
                                self.byts = bytearray(fbin.read(nbyts))
                                enable = True
                elif self.modebox.GetSelection() == 2:
                    enable = True
        if enable:
            self.gobutton.Enable()
        else:
            self.gobutton.Disable()
        self.Layout()

    def OnModeChange(self, _event):
        if self.modebox.GetSelection() == 0:
            self.gobutton.SetLabel("Read")
            self.writefpicker.Hide()
            self.formatbox.Hide()
            self.readfpicker.Show()
            self.wfilel.Show()
            self.progressboxp.Show()
        elif self.modebox.GetSelection() == 1:
            self.gobutton.SetLabel("Write")
            self.writefpicker.Show()
            self.formatbox.Hide()
            self.readfpicker.Hide()
            self.wfilel.Show()
            self.progressboxp.Show()
        else:
            self.gobutton.SetLabel("Format")
            self.writefpicker.Hide()
            self.formatbox.Show()
            self.readfpicker.Hide()
            self.wfilel.Hide()
            self.progressboxp.Hide()
        self.OnValidateMode(None)
        self.Layout()

    def KlineWorkerHandler(self, info, value):
        if info == "read_eeprom.progress":
            if value[0] is not None and value[0] >= 0:
                self.progress.SetValue(value[0])
            if value[1] and value[1] == "interrupted":
                self.progressboxp.Hide()
                wx.MessageDialog(None, 'Read EEPROM interrupted', "", wx.CENTRE | wx.STAY_ON_TOP).ShowModal()
            self.progress_text.SetLabel("Reading EEPROM")
            wx.CallAfter(self.OnModeChange, None)
        elif info == "read_eeprom.result":
            wx.MessageDialog(None, 'Read EEPROM complete', "", wx.CENTRE | wx.STAY_ON_TOP).ShowModal()
            self.progress_text.SetLabel("")
            self.progress.SetValue(0)
        elif info == "write_eeprom.progress":
            if value[0] is not None and value[0] >= 0:
                self.progress.SetValue(value[0])
            if value[1] and value[1] == "interrupted":
                self.progressboxp.Hide()
                wx.MessageDialog(None, 'Write EEPROM interrupted', "", wx.CENTRE | wx.STAY_ON_TOP).ShowModal()
            self.progress_text.SetLabel("Writing EEPROM")
            wx.CallAfter(self.OnModeChange, None)
        elif info == "write_eeprom.result":
            wx.MessageDialog(None, 'Write EEPROM complete', "", wx.CENTRE | wx.STAY_ON_TOP).ShowModal()
            self.progress_text.SetLabel("")
            self.progress.SetValue(0)
            wx.CallAfter(self.OnModeChange, None)
        elif info == "format_eeprom":
            self.progress_text.SetLabel("")
            self.progress.SetValue(0)
            wx.CallAfter(self.OnModeChange, None)
        elif info == "format_eeprom.result":
            wx.MessageDialog(None, 'Format EEPROM complete', "", wx.CENTRE | wx.STAY_ON_TOP).ShowModal()
            self.progress_text.SetLabel("")
            self.progress.SetValue(0)
            wx.CallAfter(self.OnModeChange, None)
        elif info == "state":
            wx.CallAfter(self.OnModeChange, None)
