import json
import os
import tarfile

import wx
from eculib.honda import *

from .base import HondaECU_AppPanel


class HondaECU_FlashPanel(HondaECU_AppPanel):

    def Build(self):
        if self.parent.nobins:
            self.wildcard = "HondaECU tune file (*.htf)|*.htf"
        else:
            self.wildcard = "HondaECU supported files (*.htf,*.bin)|*.htf;*.bin|HondaECU tune file (*.htf)|*.htf|ECU dump (*.bin)|*.bin"
        self.byts = None

        self.mainp = wx.Panel(self)
        self.wfilel = wx.StaticText(self.mainp, label="File")
        self.readfpicker = wx.FilePickerCtrl(self.mainp, wildcard="ECU dump (*.bin)|*.bin",
                                             style=wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL)
        self.writefpicker = wx.FilePickerCtrl(self.mainp, wildcard=self.wildcard,
                                              style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL)
        self.optsp = wx.Panel(self.mainp)
        self.wchecksuml = wx.StaticText(self.optsp, label="Checksum Location")
        self.fixchecksum = wx.CheckBox(self.optsp, label="Fix")
        self.checksum = wx.TextCtrl(self.optsp)
        self.offsetl = wx.StaticText(self.optsp, label="Start Offset")
        self.offset = wx.TextCtrl(self.optsp)
        self.offset.SetValue("0x0")
        self.htfoffset = None

        self.gobutton = wx.Button(self.mainp, label="Read")
        self.gobutton.Disable()
        self.checksum.Disable()

        self.optsbox = wx.BoxSizer(wx.HORIZONTAL)
        self.optsbox.Add(self.offsetl, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=10)
        self.optsbox.Add(self.offset, 0, flag=wx.LEFT, border=5)
        self.optsbox.Add(self.wchecksuml, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=10)
        self.optsbox.Add(self.checksum, 0, flag=wx.LEFT, border=5)
        self.optsbox.Add(self.fixchecksum, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=10)
        self.optsp.SetSizer(self.optsbox)

        self.fpickerbox = wx.BoxSizer(wx.HORIZONTAL)
        self.fpickerbox.AddSpacer(5)
        self.fpickerbox.Add(self.readfpicker, 1)
        self.fpickerbox.Add(self.writefpicker, 1)

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

        self.modebox = wx.RadioBox(self.mainp, label="Mode", choices=["Read", "Write"])

        self.flashpsizer = wx.GridBagSizer()
        self.flashpsizer.Add(self.wfilel, pos=(0, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
                             border=10)
        self.flashpsizer.Add(self.fpickerbox, pos=(0, 1), span=(1, 5), flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=10)
        self.flashpsizer.Add(self.optsp, pos=(1, 0), span=(1, 6))
        self.flashpsizer.Add(self.progressboxp, pos=(3, 0), span=(1, 6),
                             flag=wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND | wx.TOP, border=20)
        self.flashpsizer.Add(self.modebox, pos=(4, 0), span=(1, 2), flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.TOP | wx.LEFT,
                             border=30)
        self.flashpsizer.Add(self.gobutton, pos=(5, 5), flag=wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.RIGHT, border=10)
        self.flashpsizer.AddGrowableRow(2, 1)
        self.flashpsizer.AddGrowableCol(5, 1)
        self.mainp.SetSizer(self.flashpsizer)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.mainp, 1, wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(self.mainsizer)

        self.readfpicker.Hide()
        # self.mainsizer.SetSizeHints(self)
        # self.SetSizer(self.mainsizer)
        # self.SetSizeHints(self.mainp)
        # self.mainsizer.Fit(self)
        self.Fit()
        self.Layout()

        self.OnModeChange(None)

        self.offset.Bind(wx.EVT_TEXT, self.OnOffset)
        self.checksum.Bind(wx.EVT_TEXT, self.OnChecksum)
        self.readfpicker.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnReadPicker)
        self.writefpicker.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnWritePicker)
        self.fixchecksum.Bind(wx.EVT_CHECKBOX, self.OnFix)
        self.gobutton.Bind(wx.EVT_BUTTON, self.OnGo)
        self.modebox.Bind(wx.EVT_RADIOBOX, self.OnModeChange)

    def OnWriteFileSelected(self, _event):
        self.htfoffset = None
        self.doHTF = False
        if len(self.writefpicker.GetPath()) > 0:
            if os.path.splitext(self.writefpicker.GetPath())[-1] == ".htf":
                self.doHTF = True
        if self.doHTF or len(self.writefpicker.GetPath()) == 0:
            self.checksum.Hide()
            self.wchecksuml.Hide()
            self.fixchecksum.Hide()
            self.offsetl.Hide()
            self.offset.Hide()
        else:
            self.checksum.Show()
            self.wchecksuml.Show()
            self.fixchecksum.Show()
            self.offsetl.Show()
            self.offset.Show()
        self.Layout()

    def OnOffset(self, _event):
        self.OnValidateMode(None)

    def OnChecksum(self, _event):
        self.OnValidateMode(None)

    def OnReadPicker(self, _event):
        self.OnValidateMode(None)

    def OnWritePicker(self, _event):
        self.OnWriteFileSelected(None)
        self.OnValidateMode(None)

    def OnFix(self, _event):
        if self.fixchecksum.IsChecked():
            self.checksum.Enable()
        else:
            self.checksum.Disable()
        self.OnValidateMode(None)

    def OnModeChange(self, _event):
        if self.modebox.GetSelection() == 0:
            self.gobutton.SetLabel("Read")
            self.writefpicker.Hide()
            self.readfpicker.Show()
            self.checksum.Hide()
            self.wchecksuml.Hide()
            self.fixchecksum.Hide()
            self.offsetl.Show()
            self.offset.Show()
            # self.passboxp.Show()
            self.progressboxp.Show()
        else:
            # self.passboxp.Hide()
            self.progressboxp.Show()
            self.gobutton.SetLabel("Write")
            self.writefpicker.Show()
            self.readfpicker.Hide()
            self.OnWriteFileSelected(None)
        self.OnValidateMode(None)
        self.Layout()

    def KlineWorkerHandler(self, info, value):
        if info == "read.progress":
            if value[0] is not None and value[0] >= 0:
                self.progress.SetValue(value[0])
            else:
                pulse = time.time()
                if pulse - self.lastpulse > .2:
                    self.progress.Pulse()
                    self.lastpulse = pulse
            if value[1] and value[1] == "interrupted":
                self.progressboxp.Hide()
                wx.MessageDialog(None, 'Read interrupted', "", wx.CENTRE | wx.STAY_ON_TOP).ShowModal()
            self.progress_text.SetLabel("Read: " + value[1])
            wx.CallAfter(self.OnModeChange, None)
        elif info == "read.result":
            self.progress.SetValue(0)
            wx.MessageDialog(None, 'Read: complete (result=%s)' % value, "", wx.CENTRE | wx.STAY_ON_TOP).ShowModal()
            self.progressboxp.Hide()
            wx.CallAfter(self.OnModeChange, None)
        if info == "write.progress":
            if value[0] is not None and value[0] >= 0:
                self.progress.SetValue(value[0])
            else:
                pulse = time.time()
                if pulse - self.lastpulse > .2:
                    self.progress.Pulse()
                    self.lastpulse = pulse
            self.progress_text.SetLabel("Write: " + value[1])
            wx.CallAfter(self.OnModeChange, None)
        elif info == "write.result":
            self.progress.SetValue(0)
            wx.MessageDialog(None, 'Write: complete (result=%s)' % value, "", wx.CENTRE | wx.STAY_ON_TOP).ShowModal()
            wx.CallAfter(self.OnModeChange, None)
        elif info == "state":
            wx.CallAfter(self.OnModeChange, None)

    def OnGo(self, _event):
        self.gobutton.Disable()
        if self.modebox.GetSelection() == 0:
            offset = int(self.offset.GetValue(), 16)
            data = self.readfpicker.GetPath()
            self.progressboxp.Show()
            self.Layout()
            dispatcher.send(signal="ReadPanel", sender=self, data=data, offset=offset)
        else:
            if self.htfoffset != None:
                offset = int(self.htfoffset, 16)
            else:
                offset = int(self.offset.GetValue(), 16)
            self.gobutton.Disable()
            dispatcher.send(signal="WritePanel", sender=self, data=self.byts, offset=offset)

    def OnValidateMode(self, event):
        enable = False
        if "state" in self.parent.ecuinfo:
            if self.modebox.GetSelection() == 0:
                if self.parent.ecuinfo["state"] in [ECUSTATE.SECURE]:
                    offset = None
                    try:
                        offset = int(self.offset.GetValue(), 16)
                    except:
                        pass
                    enable = (len(self.readfpicker.GetPath()) > 0 and offset is not None and offset >= 0)
            else:
                if self.parent.ecuinfo["state"] in [ECUSTATE.OK, ECUSTATE.RECOVER_NEW, ECUSTATE.RECOVER_OLD,
                                                    ECUSTATE.FLASH]:
                    if self.doHTF:
                        enable = self.OnValidateModeHTF(event)
                    else:
                        enable = self.OnValidateModeBin(event)
        if enable:
            self.gobutton.Enable()
        else:
            self.gobutton.Disable()
        self.Layout()

    def OnValidateModeHTF(self, _event):
        if len(self.writefpicker.GetPath()) > 0:
            if os.path.isfile(self.writefpicker.GetPath()):
                tar = tarfile.open(self.writefpicker.GetPath(), "r:xz")
                binmod = None
                metainfo = None
                for f in tar.getnames():
                    if f == "metainfo.json":
                        metainfo = json.load(tar.extractfile(f))
                    else:
                        b, e = os.path.splitext(f)
                        if e == ".bin":
                            x, y = os.path.splitext(b)
                            if y == ".mod":
                                binmod = bytearray(tar.extractfile(f).read())
                if binmod is not None and metainfo is not None:
                    ea = int(metainfo["ecmidaddr"], 16)
                    ka = int(metainfo["keihinaddr"], 16)
                    if "offset" in metainfo:
                        self.htfoffset = metainfo["offset"]
                    if "rid" in metainfo and metainfo["rid"] is not None:
                        for i in range(5):
                            binmod[ea + i] ^= 0xFF
                        for i in range(7):
                            binmod[ka + i] = ord(metainfo["rid"][i])
                    ret, status, self.byts = do_validation(binmod, len(binmod), int(metainfo["checksum"], 16))
                    if status != "bad":
                        return True
        return False

    def OnValidateModeBin(self, _event):
        _offset = None
        try:
            _offset = int(self.offset.GetValue(), 16)
        except:
            return False
        checksum = -1
        if self.fixchecksum.IsChecked():
            try:
                checksum = int(self.checksum.GetValue(), 16)
            except:
                return False
        if len(self.writefpicker.GetPath()) > 0:
            if os.path.isfile(self.writefpicker.GetPath()):
                fbin = open(self.writefpicker.GetPath(), "rb")
                nbyts = os.path.getsize(self.writefpicker.GetPath())
                byts = bytearray(fbin.read(nbyts))
                fbin.close()
                if checksum >= nbyts:
                    return False
                ret, status, self.byts = do_validation(byts, nbyts, checksum)
                if status != "bad":
                    return True
        return False
