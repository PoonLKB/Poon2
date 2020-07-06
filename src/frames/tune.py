import io
import json
import math
import operator
import os
import struct
import tarfile

import colour
import numpy as np
import wx
import wx.aui
import wx.dataview as dv
import wx.grid as gridlib
import wx.lib.agw.aui.auibook
from lxml import etree
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf)

red = colour.Color("blue")
colors = list(red.range_to(colour.Color("red"), 100))
colors = [wx.Colour(c.red * 255, c.green * 255, c.blue * 255) for c in colors]


class NumericStringParser(object):
    '''
    Most of this code comes from the fourFn.py pyparsing example

    '''

    def pushFirst(self, strg, loc, toks):
        self.exprStack.append(toks[0])

    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0] == '-':
            self.exprStack.append('unary -')

    def __init__(self):
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(Word("+-" + nums, nums) +
                          Optional(point + Optional(Word(nums))) +
                          Optional(e + Word("+-" + nums, nums)))
        ident = Word(alphas, alphas + nums + "_$")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                 (ident + lpar + expr + rpar | pi | e | fnumber).setParseAction(self.pushFirst))
                | Optional(oneOf("- +")) + Group(lpar + expr + rpar)
                ).setParseAction(self.pushUMinus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + \
        ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor + \
               ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        expr << term + \
        ZeroOrMore((addop + term).setParseAction(self.pushFirst))
        # addop_term = ( addop + term ).setParseAction( self.pushFirst )
        # general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        # expr <<  general_term
        self.bnf = expr
        # map operator symbols to corresponding arithmetic operations
        epsilon = 1e-12
        self.opn = {"+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": operator.truediv,
                    "^": operator.pow}
        self.fn = {"sin": math.sin,
                   "cos": math.cos,
                   "tan": math.tan,
                   "exp": math.exp,
                   "abs": abs,
                   "trunc": lambda a: int(a),
                   "round": round,
                   "sgn": lambda a: abs(a) > epsilon and cmp(a, 0) or 0}

    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluateStack(s)
        if op in "+-*/^":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op](self.evaluateStack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string, parseAll=True):
        self.exprStack = []
        results = self.bnf.parseString(num_string, parseAll)
        val = self.evaluateStack(self.exprStack[:])
        return val


nsp = NumericStringParser()


def get_table_info(t):
    n = t.xpath("title")[0].text
    # x-axis
    xxx = t.xpath("XDFAXIS[@id='x']")[0]
    xindexcount = int(xxx.xpath("indexcount")[0].text)
    e = xxx.xpath("embedinfo")
    if len(e) > 0:
        xtype = int(e[0].get("type"))
        xlinkobjid = e[0].get("linkobjid")
    else:
        xtype = None
        xlinkobjid = None
    xot = xxx.xpath("outputtype")
    if len(xot) > 0:
        xot = xot[0].text
    else:
        xot = None
    xdp = xxx.xpath("decimalpl")
    if len(xdp) > 0:
        xdp = xdp[0].text
    else:
        xdp = None
    # y-axis
    yyy = t.xpath("XDFAXIS[@id='y']")[0]
    yindexcount = int(yyy.xpath("indexcount")[0].text)
    e = yyy.xpath("embedinfo")
    if len(e) > 0:
        ytype = int(e[0].get("type"))
        ylinkobjid = e[0].get("linkobjid")
    else:
        ytype = None
        ylinkobjid = None
    yot = yyy.xpath("outputtype")
    if len(yot) > 0:
        yot = yot[0].text
    else:
        yot = None
    ydp = yyy.xpath("decimalpl")
    if len(ydp) > 0:
        ydp = ydp[0].text
    else:
        ydp = None
    # z-axis
    zzz = t.xpath("XDFAXIS[@id='z']")[0]
    m = zzz.xpath("MATH")
    if len(m) > 0:
        eq = m[0].get('equation')
    else:
        eq = None
    zot = zzz.xpath("outputtype")
    if len(zot) > 0:
        zot = zot[0].text
    else:
        zot = None
    zdp = zzz.xpath("decimalpl")
    if len(zdp) > 0:
        zdp = zdp[0].text
    else:
        zdp = None
    zmin = zzz.xpath("min")
    if len(zmin) > 0:
        zmin = zmin[0].text
    else:
        zmax = None
    zmax = zzz.xpath("max")
    if len(zmax) > 0:
        zmax = zmax[0].text
    else:
        zmax = None
    e = zzz.xpath("EMBEDDEDDATA")[0]
    a = int(e.get("mmedaddress"), 16)
    s = int(e.get("mmedelementsizebits"))
    ff = e.get("mmedtypeflags")
    if ff != None:
        ff = int(ff, 16)
    else:
        ff = 0
    ff = "<" if (ff & 0x02) else ">"
    ######
    axisinfo = {
        'x': {'indexcount': xindexcount, 'type': xtype, 'linkobjid': xlinkobjid, 'xot': xot, 'xdp': xdp},
        # 'xmin': xmin, 'xmax': xmax},
        'y': {'indexcount': yindexcount, 'type': ytype, 'linkobjid': ylinkobjid, 'yot': yot, 'ydp': ydp},
        # 'ymin': ymin, 'ymax': ymax},
        'z': {'eq': eq, 'zot': zot, 'zdp': zdp, 'zmin': zmin, 'zmax': zmax, 'lsb': ff}
    }
    return n, a, s, axisinfo


class Table(object):

    def __init__(self, name, address, stride, axisinfo, parent, uniqueid=None, flags=0, categories=[], metainfo=None):
        self.name = name
        self.address = address
        self.stride = stride
        self.axisinfo = axisinfo
        self.parent = parent
        self.uniqueid = uniqueid
        self.flags = flags
        self.categories = categories
        self.metainfo = metainfo

    def __repr__(self):
        return 'Table: ' + self.name


class Folder(object):

    def __init__(self, id, label):
        self.id = id
        self.label = label
        self.children = []

    def __repr__(self):
        return 'Folder: ' + self.label


class XDFModel(dv.PyDataViewModel):

    def __init__(self, parent, xdf):
        dv.PyDataViewModel.__init__(self)
        self.parent = parent
        self.foldericon = wx.Icon(os.path.join(self.parent.parent.basepath, "images/folder.png"), wx.BITMAP_TYPE_ANY)
        self.tableicon = wx.Icon(os.path.join(self.parent.parent.basepath, "images/table.png"), wx.BITMAP_TYPE_ANY)
        categories = {}
        for c in xdf.xpath('/XDFFORMAT/XDFHEADER/CATEGORY'):
            categories[c.get("index")] = c.get("name")
        self.uids = {}
        self.data = {"0.0.0": Folder("0.0.0", "")}
        cats = []
        for t in xdf.xpath('/XDFFORMAT/XDFTABLE'):
            uid = t.get("uniqueid")
            flags = int(t.get("flags"), 16)
            parent = ["0", "0", "0"]
            c0 = t.xpath('CATEGORYMEM[@index=0]')
            if len(c0) > 0:
                parent[0] = c0[0].get("category")
                p = ".".join(parent)
                if not p in self.data:
                    self.data[p] = Folder(p, categories["0x%X" % (int(parent[0]) - 1)])
                    cats.append(self.data[p].label)
            c1 = t.xpath('CATEGORYMEM[@index=1]')
            if len(c1) > 0:
                parent[1] = c1[0].get("category")
                p = ".".join(parent)
                if not p in self.data:
                    self.data[p] = Folder(p, categories["0x%X" % (int(parent[1]) - 1)])
                    cats.append(self.data[p].label)
                pp = ["0", "0", "0"]
                pp[0] = parent[0]
                pp = ".".join(pp)
                if not self.data[p] in self.data[pp].children:
                    self.data[pp].children.append(self.data[p])
            c2 = t.xpath('CATEGORYMEM[@index=2]')
            if len(c2) > 0:
                parent[2] = c2[0].get("category")
                p = ".".join(parent)
                if not p in self.data:
                    self.data[p] = Folder(p, categories["0x%X" % (int(parent[2]) - 1)])
                    cats.append(self.data[p].label)
                pp = ["0", "0", "0"]
                pp[0] = parent[0]
                pp[1] = parent[1]
                pp = ".".join(pp)
                if not self.data[p] in self.data[pp].children:
                    self.data[pp].children.append(self.data[p])
            pp = ".".join(parent)
            n, a, s, i = get_table_info(t)
            self.data[pp].children.append(
                Table(n, a, s, i, pp, uniqueid=uid, flags=flags, categories=cats, metainfo=self.parent.metainfo))
            self.uids[uid] = self.data[pp].children[-1]
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        return 1

    def GetColumnType(self, col):
        mapper = {0: 'string'}
        return mapper[col]

    def GetChildren(self, parent, children):
        if not parent:
            childs = []
            for c in self.data.keys():
                c0, c1, c2 = c.split(".")
                if c0 != "0":
                    if c1 == "0" and c2 == "0":
                        childs.append(c)
                        children.append(self.ObjectToItem(self.data[c]))
                elif c == "0.0.0":
                    for c in self.data[c].children:
                        childs.append(c)
                        children.append(self.ObjectToItem(c))
            return len(childs)
        else:
            node = self.ItemToObject(parent)
            childs = []
            for c in node.children:
                childs.append(c)
                children.append(self.ObjectToItem(c))
            return len(childs)
        return 0

    def IsContainer(self, item):
        if not item:
            return True
        node = self.ItemToObject(item)
        if isinstance(node, Folder):
            return True
        return False

    def GetValue(self, item, col):
        node = self.ItemToObject(item)
        if isinstance(node, Folder):
            return dv.DataViewIconText(text=node.label, icon=self.foldericon)
        elif isinstance(node, Table):
            return dv.DataViewIconText(text=node.name, icon=self.tableicon)

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Folder):
            nid0, nid1, nid2 = node.id.split(".")
            if nid0 != "0":
                if nid1 == "0" and nid2 == "0":
                    return dv.NullDataViewItem
                elif nid1 != "0" and nid2 == "0":
                    pp = ["0", "0", "0"]
                    pp[0] = nid0
                    pp = ".".join(pp)
                    return self.ObjectToItem(self.data[pp])
                elif nid1 != "0" and nid2 != "0":
                    pp = ["0", "0", "0"]
                    pp[0] = nid0
                    pp[1] = nid1
                    pp = ".".join(pp)
                    return self.ObjectToItem(self.data[pp])
        elif isinstance(node, Table):
            if node.parent == "0.0.0":
                return dv.NullDataViewItem
            else:
                return self.ObjectToItem(self.data[node.parent])

    def HasDefaultCompare(self):
        return False

    def Compare(self, item1, item2, column, ascending):
        ascending = 1 if ascending else -1
        item1 = self.ItemToObject(item1)
        item2 = self.ItemToObject(item2)
        if isinstance(item1, Folder):
            if isinstance(item2, Folder):
                ret = 0
            elif isinstance(item2, Table):
                ret = -1
        elif isinstance(item1, Table):
            if isinstance(item2, Folder):
                ret = 1
            elif isinstance(item2, Table):
                ret = 0
        return ret * ascending


class XDFGridTable(wx.grid.GridTableBase):

    def __init__(self, uids, byts, bin, node):
        wx.grid.GridTableBase.__init__(self)
        self.dirty = False
        self.address = node.address
        self.stride = node.stride
        self.axisinfo = node.axisinfo
        self.flags = node.flags
        self.categories = node.categories
        self.metainfo = node.metainfo
        self.restriction = None
        if self.metainfo["restriction"] != None and self.metainfo["restrictions"] != None:
            self.restriction = self.metainfo["restrictions"][list(self.metainfo["restrictions"].keys())[0]]
        rows = self.axisinfo['y']['indexcount']
        cols = self.axisinfo['x']['indexcount']
        zzt = self.axisinfo['z']['lsb']
        s = "B"
        if self.stride == 16:
            s = "H"
        self.origdata = np.array(struct.unpack_from("%s%d%s" % (zzt, rows * cols, s), bin, offset=self.address))
        self.data = np.array(struct.unpack_from("%s%d%s" % (zzt, rows * cols, s), byts, offset=self.address))
        if not self.axisinfo['z']['eq'] is None:
            def formatCell(x):
                x = nsp.eval(self.axisinfo['z']['eq'].replace("X", str(x)))
                if self.axisinfo['z']['zot'] == "0":
                    if self.stride == 16:
                        return "%04X" % (x)
                    else:
                        return "%02X" % (x)
                elif self.axisinfo['z']['zot'] == "1":
                    if not self.axisinfo['z']['zdp'] is None:
                        dp = int(self.axisinfo['z']['zdp'])
                        return "%s" % (round(x, dp))
                    return "%s" % (float(x))
                elif self.axisinfo['z']['zot'] == "2":
                    return "%s" % (x)

            self.data = np.vectorize(formatCell)(self.data)
            self.origdata = np.vectorize(formatCell)(self.origdata)
        self.data = self.data.reshape(rows, cols)
        self.origdata = self.origdata.reshape(rows, cols)

        self.cols = None
        if "linkobjid" in self.axisinfo["x"]:
            x = self.axisinfo["x"]["linkobjid"]
            if not x is None:
                xx = uids[x]
                sx = "B"
                if xx.stride == 16:
                    sx = "H"
                xxrows = xx.axisinfo['y']['indexcount']
                xxcols = xx.axisinfo['x']['indexcount']
                xxt = xx.axisinfo['z']['lsb']
                self.cols = np.array(
                    struct.unpack_from("%s%d%s" % (xxt, xxrows * xxcols, sx), byts, offset=xx.address)).reshape(xxrows,
                                                                                                                xxcols)
                if not xx.axisinfo['z']['eq'] is None:
                    def formatCell(x):
                        x = nsp.eval(xx.axisinfo['z']['eq'].replace("X", str(x)))
                        if xx.axisinfo['z']['zot'] == "0":
                            return chr(x)
                        elif xx.axisinfo['z']['zot'] == "1":
                            if not xx.axisinfo['z']['zdp'] is None:
                                return round(x, int(xx.axisinfo['z']['zdp']))
                            return float(x)
                        elif xx.axisinfo['z']['zot'] == "2":
                            return int(x)

                    self.cols = np.vectorize(formatCell)(self.cols)
        self.rows = None
        if "linkobjid" in self.axisinfo["y"]:
            y = self.axisinfo["y"]["linkobjid"]
            if not y is None:
                yy = uids[y]
                sy = "B"
                if yy.stride == 16:
                    sy = "H"
                yyrows = yy.axisinfo['y']['indexcount']
                yycols = yy.axisinfo['x']['indexcount']
                yyt = yy.axisinfo['z']['lsb']
                self.rows = np.array(
                    struct.unpack_from("%s%d%s" % (yyt, yyrows * yycols, sy), byts, offset=yy.address)).reshape(yyrows,
                                                                                                                yycols)
                if not yy.axisinfo['z']['eq'] is None:
                    def formatCell(y):
                        y = nsp.eval(yy.axisinfo['z']['eq'].replace("X", str(y)))
                        if yy.axisinfo['z']['zot'] == "0":
                            return chr(y)
                        elif yy.axisinfo['z']['zot'] == "1":
                            if not yy.axisinfo['z']['zdp'] is None:
                                return round(y, int(yy.axisinfo['z']['zdp']))
                            return float(y)
                        elif yy.axisinfo['z']['zot'] == "2":
                            return int(y)

                    self.rows = np.vectorize(formatCell)(self.rows)

    def PackData(self, byts):
        d = self.data.flatten()
        if not self.axisinfo['z']['eq'] is None:
            eq = self.axisinfo['z']['eq'].replace("/", "|").replace("*", "/").replace("|", "*").replace("-",
                                                                                                        "|").replace(
                "+", "-").replace("|", "+")

            def formatCell(x):
                if self.axisinfo['z']['zot'] == "0":
                    x = ord(x)
                return int(np.ceil(nsp.eval(eq.replace("X", str(x)))))

            d = np.vectorize(formatCell)(d)
        s = "B"
        if self.stride == 16:
            s = "H"
        struct.pack_into("%s%d%s" % (self.lsb, self.axisinfo['y']['indexcount'] * self.axisinfo['x']['indexcount'], s),
                         byts, self.address, *d)

    def GetNumberRows(self):
        return self.data.shape[0]

    def GetNumberCols(self):
        return self.data.shape[1]

    def IsEmptyCell(self, row, col):
        return False

    def SetValue(self, row, col, value):
        if self.restriction is None:
            self.dirty = True
            self.data[row][col] = value
        else:
            od = float(self.origdata[row][col])
            delta = float(value) - od
            if delta < 0:
                if delta < self.restriction[0]:
                    delta = self.restriction[0]
            elif delta > 0:
                if delta > self.restriction[1]:
                    delta = self.restriction[1]
            nd = "%s" % (float(od + delta))
            self.data[row][col] = nd
            self.dirty = True

    def GetValue(self, row, col):
        return self.data[row][col]

    def GetTypeName(self, row, col):
        return wx.grid.GRID_VALUE_STRING

    def GetColLabelValue(self, col):
        if not self.cols is None:
            return str(self.cols[col][0])
        return str(col)

    def GetRowLabelValue(self, row):
        if not self.rows is None:
            return str(self.rows[row][0])
        return str(row)

    def GetAttr(self, row, col, kind):
        attr = wx.grid.GridCellAttr()
        if self.flags & 0x30 and not self.axisinfo['z']['zmin'] is None and not self.axisinfo['z']['zmax'] is None:
            attr.SetBackgroundColour(colors[int(
                np.interp(self.data[row][col], [self.axisinfo['z']['zmin'], self.axisinfo['z']['zmax']], [0, 99]))])
        return attr


class MyGrid(wx.grid.Grid):
    """ A Copy&Paste enabled grid class"""

    def __init__(self, parent):
        wx.grid.Grid.__init__(self, parent)
        # wx.EVT_KEY_DOWN(self, self.OnKey)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.data4undo = [0, 0, '']

    def OnKey(self, event):
        # If Ctrl+C is pressed...
        if event.ControlDown() and event.GetKeyCode() == 67:
            self.copy()
        # If Ctrl+V is pressed...
        if event.ControlDown() and event.GetKeyCode() == 86:
            self.paste('clip')
        # If Ctrl+Z is pressed...
        if event.ControlDown() and event.GetKeyCode() == 90:
            if self.data4undo[2] != '':
                self.paste('undo')
        # If del is pressed...
        if event.GetKeyCode() == 127:
            # Call delete method
            self.delete()
        # Skip other Key events
        if event.GetKeyCode():
            event.Skip()
            return

    def copy(self):
        # Number of rows and cols
        topleft = self.GetSelectionBlockTopLeft()
        if list(topleft) == []:
            topleft = []
        else:
            topleft = list(topleft[0])
        bottomright = self.GetSelectionBlockBottomRight()
        if list(bottomright) == []:
            bottomright = []
        else:
            bottomright = list(bottomright[0])
        if list(self.GetSelectionBlockTopLeft()) == []:
            rows = 1
            cols = 1
            iscell = True
        else:
            rows = bottomright[0] - topleft[0] + 1
            cols = bottomright[1] - topleft[1] + 1
            iscell = False
        # data variable contain text that must be set in the clipboard
        data = ''
        # For each cell in selected range append the cell value in the data variable
        # Tabs '    ' for cols and '\r' for rows
        for r in range(rows):
            for c in range(cols):
                if iscell:
                    data += str(self.GetCellValue(self.GetGridCursorRow() + r, self.GetGridCursorCol() + c))
                else:
                    data += str(self.GetCellValue(topleft[0] + r, topleft[1] + c))
                if c < cols - 1:
                    data += '    '
            data += '\n'
        # Create text data object
        clipboard = wx.TextDataObject()
        # Set data object value
        clipboard.SetText(data)
        # Put the data in the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")

    def paste(self, stage):
        topleft = list(self.GetSelectionBlockTopLeft())
        if stage == 'clip':
            clipboard = wx.TextDataObject()
            if wx.TheClipboard.Open():
                wx.TheClipboard.GetData(clipboard)
                wx.TheClipboard.Close()
            else:
                wx.MessageBox("Can't open the clipboard", "Error")
            data = clipboard.GetText()
            if topleft == []:
                rowstart = self.GetGridCursorRow()
                colstart = self.GetGridCursorCol()
            else:
                rowstart = topleft[0][0]
                colstart = topleft[0][1]
        elif stage == 'undo':
            data = self.data4undo[2]
            rowstart = self.data4undo[0]
            colstart = self.data4undo[1]
        else:
            wx.MessageBox("Paste method " + stage + " does not exist", "Error")
        text4undo = ''
        # Convert text in a array of lines
        for y, r in enumerate(data.splitlines()):
            # Convert c in a array of text separated by tab
            for x, c in enumerate(r.split('    ')):
                if y + rowstart < self.NumberRows and x + colstart < self.NumberCols:
                    text4undo += str(self.GetCellValue(rowstart + y, colstart + x)) + '    '
                    self.SetCellValue(rowstart + y, colstart + x, c)
            text4undo = text4undo[:-1] + '\n'
        if stage == 'clip':
            self.data4undo = [rowstart, colstart, text4undo]
        else:
            self.data4undo = [0, 0, '']

    def delete(self):
        # print "Delete method"
        # Number of rows and cols
        topleft = list(self.GetSelectionBlockTopLeft())
        bottomright = list(self.GetSelectionBlockBottomRight())
        if topleft == []:
            rows = 1
            cols = 1
        else:
            rows = bottomright[0][0] - topleft[0][0] + 1
            cols = bottomright[0][1] - topleft[0][1] + 1
        # Clear cells contents
        for r in range(rows):
            for c in range(cols):
                if topleft == []:
                    self.SetCellValue(self.GetGridCursorRow() + r, self.GetGridCursorCol() + c, '')
                else:
                    self.SetCellValue(topleft[0][0] + r, topleft[0][1] + c, '')


class TablePanel(wx.Panel):

    def __init__(self, parent, node):
        self.parent = parent
        self.node = node
        self.uid = node.uniqueid
        wx.Panel.__init__(self, parent)
        self.tb = wx.ToolBar(self)
        save = wx.Image(os.path.join(self.parent.parent.basepath, "images/save.png"),
                        wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        sb = self.tb.AddTool(wx.ID_SAVE, "Save", save)
        self.tb.Realize()
        self.Bind(wx.EVT_MENU, self.OnSave, sb)
        self.tb.EnableTool(wx.ID_SAVE, False)
        self.g = MyGrid(self)
        self.gt = XDFGridTable(self.parent.ptreemodel.uids, self.parent.byts, self.parent.bin, node)
        self.g.SetTable(self.gt, True)
        self.g.AutoSize()
        for c in range(node.axisinfo['x']['indexcount']):
            self.g.DisableDragColSize()
            self.g.DisableColResize(c)
            self.g.AutoSizeColLabelSize(c)
        for r in range(node.axisinfo['y']['indexcount']):
            self.g.DisableDragRowSize()
            self.g.DisableRowResize(r)
            self.g.AutoSizeRowLabelSize(r)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tb, 0)
        sizer.Add(self.g, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.g.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChanged)

    def OnSave(self, event):
        self.gt.PackData(self.parent.byts)
        self.parent.dirty = True
        self.tb.EnableTool(wx.ID_SAVE, False)

    def OnCellChanged(self, event):
        self.dirty = True
        self.tb.EnableTool(wx.ID_SAVE, self.dirty)


class TunePanel(wx.Frame):

    def __init__(self, parent, metainfo, xdf, binorig, binmod=None):
        restrictions = ""
        if metainfo["restriction"] != None and metainfo["restrictions"] != None:
            restrictions = " | Restrictions: " + metainfo["restriction"]
        wx.Frame.__init__(self, parent, title="%s (%s) - %s%s" % (
            metainfo["model"], metainfo["year"], metainfo["ecupn"], restrictions))
        self.SetMinSize((800, 600))
        self.parent = parent
        self.metainfo = metainfo
        self.xdf = xdf
        self.bin = binorig
        self.byts = binmod
        self.currenthtf = None
        self.dirty = False
        if self.byts == None:
            self.byts = bytearray()
            self.byts[:] = self.bin
        xdftree = etree.fromstring(self.xdf)

        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
        fileMenu = wx.Menu()
        self.menubar.Append(fileMenu, '&File')
        self.saveItem = wx.MenuItem(fileMenu, wx.ID_SAVE, '&Save\tCtrl+S')
        self.Bind(wx.EVT_MENU, self.OnSave, self.saveItem)
        self.saveAsItem = wx.MenuItem(fileMenu, wx.ID_SAVEAS, 'Save As')
        self.Bind(wx.EVT_MENU, self.OnSaveAs, self.saveAsItem)
        fileMenu.Append(self.saveItem)
        fileMenu.Append(self.saveAsItem)
        fileMenu.AppendSeparator()
        quitItem = wx.MenuItem(fileMenu, wx.ID_EXIT, '&Quit\tCtrl+Q')
        self.Bind(wx.EVT_MENU, self.OnClose, quitItem)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        fileMenu.Append(quitItem)
        self.menubar.Enable(wx.ID_SAVE, 0)

        self.mgr = wx.aui.AuiManager(self)

        self.ptreep = wx.Panel(self)
        ptreesizer = wx.BoxSizer(wx.VERTICAL)
        self.ptree = wx.dataview.DataViewCtrl(self.ptreep, style=dv.DV_NO_HEADER)
        self.ptreemodel = XDFModel(self, xdftree)
        self.ptree.AssociateModel(self.ptreemodel)
        self.c0 = self.ptree.AppendIconTextColumn("Parameter Tree", 0)
        self.c0.SetSortOrder(True)
        self.ptreemodel.Resort()
        ptreesizer.Add(self.ptree, 1, wx.EXPAND)
        self.ptreep.SetSizer(ptreesizer)
        info1 = wx.aui.AuiPaneInfo().Left()
        info1.MinSize(wx.Size(200, 200))
        info1.Caption("Parameter Tree")
        self.mgr.AddPane(self.ptreep, info1)

        self.nbp = wx.Panel(self)
        self.nb = wx.lib.agw.aui.auibook.AuiNotebook(self.nbp)
        self.nb.AddTabAreaButton(wx.aui.AUI_BUTTON_WINDOWLIST, wx.RIGHT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.nbp.SetSizer(sizer)
        info2 = wx.aui.AuiPaneInfo().CenterPane()
        self.mgr.AddPane(self.nbp, info2)

        self.nb.AddPage(wx.Panel(self), "")
        self.Layout()
        self.mgr.Update()
        self.Center()
        self.nb.DeletePage(0)

        self.open_tables = {}
        self.currentSelection = wx.CallAfter(self.nb.GetSelection)
        self.nb.Bind(wx.lib.agw.aui.auibook.EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnTableClose)
        self.nb.Bind(wx.lib.agw.aui.auibook.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnTableChanged)
        self.nb.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.TableSelectedHandler)

        wx.CallAfter(self.Show)

    def OnSize(self, event):
        w, h = self.ptree.GetSize()
        self.c0.SetWidth(w)

    def OnClose(self, event):
        self.Destroy()

    def doSaveData(self):
        htf = io.BytesIO()
        with tarfile.open(mode="w:xz", fileobj=htf) as tar_handle:
            t = tarfile.TarInfo(name="metainfo.json")
            metainfo = bytearray(json.dumps(self.metainfo), 'utf8')
            t.size = len(metainfo)
            tar_handle.addfile(tarinfo=t, fileobj=io.BytesIO(metainfo))
            t = tarfile.TarInfo(name="-".join(self.metainfo["ecupn"].split("-")[:2]) + ".xdf")
            t.size = len(self.xdf)
            tar_handle.addfile(tarinfo=t, fileobj=io.BytesIO(self.xdf))
            t = tarfile.TarInfo(name=self.metainfo["ecupn"] + ".orig.bin")
            t.size = len(self.bin)
            tar_handle.addfile(tarinfo=t, fileobj=io.BytesIO(self.bin))
            t = tarfile.TarInfo(name=self.metainfo["ecupn"] + ".mod.bin")
            t.size = len(self.byts)
            tar_handle.addfile(tarinfo=t, fileobj=io.BytesIO(self.byts))
        with open(self.currenthtf, "wb") as f:
            f.write(htf.getvalue())

    def OnSave(self, event):
        self.doSaveData()

    def OnSaveAs(self, event):
        with wx.FileDialog(self, "HondaECU :: Save tune file", wildcard="HondaECU tune file (*.htf)|*.htf",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.currenthtf = fileDialog.GetPath()
            self.menubar.Enable(wx.ID_SAVE, 1)
            self.doSaveData()

    def OnTableChanged(self, event):
        self.currentSelection = self.nb.GetSelection()

    def OnTableClose(self, event):
        if self.currentSelection != None:
            p = self.nb.GetPage(self.currentSelection)
            if p.uid in self.open_tables:
                del self.open_tables[p.uid]
        self.currentSelection = self.nb.GetSelection()

    def TableSelectedHandler(self, event):
        node = self.ptreemodel.ItemToObject(event.GetItem())
        if isinstance(node, Table):
            if not node.uniqueid in self.open_tables:
                self.open_tables[node.uniqueid] = TablePanel(self, node)
                self.nb.AddPage(self.open_tables[node.uniqueid], node.name, select=True)
            else:
                self.nb.SetSelectionToWindow(self.open_tables[node.uniqueid])
