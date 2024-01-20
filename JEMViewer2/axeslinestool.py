import re
import os, json
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import matplotlib.backends.qt_editor.figureoptions as figopt
from matplotlib import colors as mcolors
from JEMViewer2.file_handler import savefile

def sorted_markers():
    all_markers = list(figopt.MARKERS.keys())
    favorite_markers = ["o","^","s","D","p","h","8","*","v","<",">","d","H","P","X","x","+"]
    sorted_markers = []
    sorted_markers.extend(favorite_markers)
    sorted_markers.extend([m for m in all_markers if m not in favorite_markers])
    return {m:figopt.MARKERS[m] for m in sorted_markers}

class IntEdit(QLineEdit):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.setFrame(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(40)
        self.setValidator(QIntValidator())
        self.changed = self.textEdited
        if initial != None:
            self.setText(str(initial))
    
    def value(self):
        try:
            return int(self.text())
        except:
            return 0

    def set(self, value):
        self.setText(str(value))

class FloatEdit(QLineEdit):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.setFrame(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(40)
        self.setValidator(QDoubleValidator())
        self.changed = self.textEdited
        if initial != None:
            self.setText(str(initial))
    
    def value(self):
        try:
            return float(self.text())
        except:
            return 0.0

    def set(self, value):
        self.setText(str(value))

    
class StrEdit(QLineEdit):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.setFrame(False)
        self.changed = self.textEdited
        if initial != None:
            self.setText(initial)

    def value(self):
        return self.text().replace("\\n", "\n")

    def set(self, value):
        self.setText(str(value))


class BoolEdit(QWidget): # centerにalignmentするためにwidgetでラップ
    changed = pyqtSignal()
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.checkbox = QCheckBox()
        layout = QHBoxLayout()
        layout.addWidget(self.checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.checkbox.clicked.connect(self.changed.emit)
        if initial != None:
            self.checkbox.setChecked(initial)

    def value(self):
        return self.checkbox.isChecked()

    def set(self, value):
        self.checkbox.setChecked(value)

class ColorButton(QPushButton):
    colorChanged = pyqtSignal(str)
    changed = pyqtSignal(str)
    def __init__(self, inicolor):
        super().__init__()
        self.clicked.connect(self._call)
        self.set_color(inicolor)
        
    def _call(self):
        color = QColorDialog().getColor(QColor(self.color))
        color = color.name()
        self.set_color(color)

    def set_color(self, color, emit=True):
        if bool(re.fullmatch(r"^#([\da-fA-F]{6})$",color)):
            self.color = color
            stylesheet = "background-color: %s;border: 1px solid; border-color: gray" % color
            self.setStyleSheet(stylesheet)
            self.colorChanged.emit(self.color)
            if emit:
                self.changed.emit(self.color)

class ColorString(StrEdit):
    textEdited_ = pyqtSignal(str)

    def __init__(self, ns, parent=None, initial=None):
        super().__init__(parent, initial)
        self.ns = ns
        self.textEdited.connect(self._text_edited)
    
    def _text_edited(self, color):
        if self.ns != None:
            if color in self.ns.keys():
                obj = self.ns[color]
                if type(obj) == str:
                    if obj[0] == "#":
                        color = obj
                        self.setText(color)
        self.textEdited_.emit(color)
        
class ColorEdit(QWidget):
    changed = pyqtSignal()
    def __init__(self, parent=None, initial=None, ns=None):
        super().__init__(parent)
        self.edit = ColorString(ns, initial=initial)
        self.edit.setFixedWidth(60)
        self.btn = ColorButton(inicolor=initial)
        self.btn.colorChanged.connect(lambda color: self.edit.setText(color))
        self.edit.textEdited_.connect(self.btn.set_color)
        self.btn.setFixedWidth(20)
        layout = QHBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.btn.changed.connect(self.changed.emit)

    def value(self):
        return self.btn.color
    
    def set(self, value):
        self.btn.set_color(value, emit=False)
        

class ComboEdit(QComboBox):
    def __init__(self, parent=None, dict=None, initial=None):
        super().__init__(parent)
        self.dict = dict
        self.invdict = {v:k for k,v in dict.items()}
        self.keyorder = list(self.invdict.keys())
        if dict != None:
            self.addItems(self.invdict.keys())
        if initial != None:
            self.setCurrentText(self.dict[initial])
        self.changed = self.activated
    
    def value(self):
        return self.invdict[self.currentText()]

    def set(self, value):
        self.setCurrentText(self.dict[value])

    def set_by_order(self, id_):
        i = id_ % len(self.keyorder)
        self.setCurrentText(self.keyorder[i])


class IntComboEdit(QComboBox):
    def __init__(self, parent=None, max=None, initial=None):
        super().__init__(parent)
        if max != None:
            self.addItems([str(i) for i in range(max)])
        if initial != None:
            self.setCurrentIndex(initial)
        self.changed = self.activated
    
    def value(self):
        return self.currentIndex()

class AliasButton(QPushButton):
    changed = pyqtSignal()
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        if initial != None:
            self.setText(initial)
    
    def value(self):
        return ""

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            # mime.setText(self.text())
            # print(mime.text())
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec_(Qt.MoveAction)


class BaseTool(QTableWidget):
    def __init__(self, figs, ns, header, title, fixsize = True):
        super().__init__()
        self.fixsize = fixsize
        self.header = header
        self.setColumnCount(len(self.header))
        self.setHorizontalHeaderLabels(self.header)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.figs = figs
        self.ns = ns
        self.setWindowTitle(title)
        # change header text color to red if selected
        self.verticalHeader().setStyleSheet("QHeaderView::section:checked{background-color:rgb(0,107,56); color:rgb(255,255,255); font-weight:bold;}")
        self.setStyleSheet("QTableWidget::item:selected{background-color:transparent;};QTableWidget::item{selection-background-color:transparent;}")

    def _allset(self, column):
        if self.rowCount() == 0: return
        for irow in range(1,self.rowCount()):
            self.cellWidget(irow,column).set(self.cellWidget(0,column).value())
            self._update(irow, column)

    def sizeHint(self):
        return QSize(150,150)

    def fit_size(self):
        if self.fixsize:
            self.setMinimumWidth(self.horizontalHeader().length()+40)
            self.setMaximumWidth(self.horizontalHeader().length()+40)
            self.setMinimumWidth(100)
            height = self.verticalHeader().length()+40
            height = height if height < 400 else 400
            self.setMinimumHeight(height)
            self.setMaximumHeight(self.verticalHeader().length()+40)
            self.setMinimumWidth(100)
        
    def appendCellWidgetToColumn(self,type,initial=None,dict=None,max=None,readonly=False):
        self.column_id += 1
        if type == "int":
            obj = IntEdit(initial=initial)
            obj.setReadOnly(readonly)
        elif type == "float":
            obj = FloatEdit(initial=initial)
        elif type == "str":
            obj = StrEdit(initial=initial)
        elif type == "bool":
            obj = BoolEdit(initial=initial)
        elif type == "combo":
            obj = ComboEdit(initial=initial,dict=dict)
        elif type == "intcombo":
            obj = IntComboEdit(initial=initial,max=max)
        elif type == "alias":
            obj = AliasButton(initial=initial)
        elif type == "color":
            obj = ColorEdit(initial=initial, ns=self.ns)
        obj.row = self.row_id
        obj.column = self.column_id
        obj.changed.connect(self.update)
        self.setCellWidget(self.row_id, self.column_id, obj)
        return obj
        
    def appendRow(self):
        self.row_id += 1
        self.insertRow(self.row_id)
        self.column_id = -1
        
    def initialize(self):
        self.setRowCount(0)
        self.row_id = -1
        self.column_id = -1

    def selectedLows(self):
        l = [i.row() for i in self.selectedIndexes()]
        return list(set(l))
        # return [i.row() for i in self.selectionModel().selectedRows()]
                
    def update(self):
        irow = self.sender().row
        icol = self.sender().column
        self._update(irow, icol)
        sl = self.selectedLows()
        if irow in sl:
            for jrow in sl:
                if jrow == irow: continue
                self.cellWidget(jrow,icol).set(self.cellWidget(irow,icol).value())
                self._update(jrow, icol)

    def gui_call(self, function_name, *args, **kwargs):
        savefile.save_emulate_command(function_name, *args, **kwargs)
        f = getattr(self, function_name)
        f(*args, **kwargs)
    

class LinesTool(BaseTool):
    line_moved = pyqtSignal()
    alias_clicked = pyqtSignal(str)
    def __init__(self, figs, ns, fixsize = True):
        header = ["show","alias","zorder","label","memo","line style","width","line color","marker","size","marker color","edge","edge color"]
        title = "LinesTool"
        super().__init__(figs, ns, header, title, fixsize)
        self.cids = {}
        self._line_draggable = False
        self.load_lines()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextmenu)
        self.legend_autoupdate(True)
        self.horizontalHeader().sectionClicked.connect(self.allset)

    def allset(self, column):
        # show context menu
        if self.header[column] in ['alias']: return
        menu = QMenu(self)
        allset_action = menu.addAction('Copy 1 to all')
        allset_action.triggered.connect(lambda: self._allset(column))
        if self.header[column] == "marker":
            allset_action = menu.addAction('Sequential set')
            allset_action.triggered.connect(lambda: self.sequential_set(column))
        menu.exec_(QCursor.pos())

    def sequential_set(self, column):
        if self.rowCount() == 0: return
        for irow in range(self.rowCount()):
            self.cellWidget(irow, column).set_by_order(irow)
            self._update(irow, column)

    def legend_autoupdate(self, b):
        self._legend_autoupdate = b

    def set_line_draggable(self, bool):
        self._line_draggable = bool

    def appendCellWidgetToColumn(self,type,initial=None,dict=None,max=None,readonly=False):
        obj = super().appendCellWidgetToColumn(type,initial,dict,max,readonly)
        if type == "alias":
            obj.clicked.connect(lambda: self.alias_clicked.emit(obj.text()))
        return obj
        
    def initialize(self):
        super().initialize()
        self.lines = []
        self.aliasbuttons = {}
        for fig in self.figs:
            if fig in self.cids:
                fig.canvas.mpl_disconnect(self.cids[fig])
        self.cids = {}
        
    def load_lines(self):
        self.initialize()
        for h, fig in enumerate(self.figs):
            self.cids[fig] = fig.canvas.mpl_connect('pick_event', self.on_pick)
            for i, ax in enumerate(fig.axes):
                for j, line in enumerate(ax.lines):
                    self.appendRow()
                    # visible
                    self.appendCellWidgetToColumn("bool", initial=line.get_visible())
                    # lines
                    btn = self.appendCellWidgetToColumn("alias", initial=f"fig{h}ax{i}l{j}")
                    self.aliasbuttons[line] = btn
                    # zorder
                    self.appendCellWidgetToColumn("int", initial=line.get_zorder())
                    # label
                    self.appendCellWidgetToColumn("str", initial=line.get_label())
                    # memo
                    self.appendCellWidgetToColumn("str", initial=line.get_gid())
                    # ls
                    self.appendCellWidgetToColumn("combo", initial=line.get_ls(), dict=figopt.LINESTYLES)
                    # lw
                    self.appendCellWidgetToColumn("float", initial=line.get_lw())
                    # lc
                    color = mcolors.to_hex(mcolors.to_rgb(line.get_color()))
                    self.appendCellWidgetToColumn("color", initial=color)
                    # marker
                    self.appendCellWidgetToColumn("combo", initial=line.get_marker(), dict=sorted_markers())
                    # markersize
                    self.appendCellWidgetToColumn("float", initial=line.get_markersize())
                    # markerfacecolor
                    facecolor = mcolors.to_hex(mcolors.to_rgb(line.get_markerfacecolor()))
                    self.appendCellWidgetToColumn("color", initial=facecolor)
                    # markeredgewidth
                    self.appendCellWidgetToColumn("float", initial=line.get_markeredgewidth())
                    # markeredgecolor
                    edgecolor = mcolors.to_hex(mcolors.to_rgb(line.get_markeredgecolor()))
                    self.appendCellWidgetToColumn("color", initial=edgecolor)
                    self.lines.append(line)
                    line.set_picker(5)
        self.resizeColumnsToContents()
        self.fit_size()

    def _update(self, irow, _):
        values = {h:self.cellWidget(irow,icol).value() for icol, h in enumerate(self.header)}
        line = self.lines[irow]
        self.gui_call("set_lineproperties", line, values)
        line.axes.figure.canvas.draw()
        
    def set_lineproperties(self, line, values):
        if type(line) == dict:
            line = savefile.dict_to_mpl(line)
        line.set_visible(values["show"])
        line.set_zorder(values["zorder"])
        line.set_label(values["label"])
        line.set_gid(values["memo"])
        line.set_ls(values["line style"])
        line.set_lw(values["width"])
        line.set_color(values["line color"])
        line.set_marker(values["marker"])
        line.set_markersize(values["size"])
        line.set_markerfacecolor(values["marker color"])
        line.set_markeredgewidth(values["edge"])
        line.set_markeredgecolor(values["edge color"])
        self.update_legend()

    def update_legend(self):
        if not self._legend_autoupdate: return
        for fig in self.figs:
            for ax in fig.axes:
                if (ol := ax.get_legend()) == None: continue
                fs = ol._fontsize
                loc = ol._loc
                drag = ol._draggable is not None
                nl = ax.legend(fontsize=fs)
                nl._set_loc(loc)
                nl.set_draggable(drag)

    def move_line(self, old_line, new_axes, delete=True):
        if type(old_line) == dict:
            old_line = savefile.dict_to_mpl(old_line)
        if new_axes != None:
            if type(new_axes) == dict:
                new_axes = savefile.dict_to_mpl(new_axes)
            new_line, = new_axes.plot(*old_line.get_data())
            new_line.set_visible(old_line.get_visible())
            new_line.set_zorder(old_line.get_zorder())
            new_line.set_label(old_line.get_label())
            new_line.set_gid(old_line.get_gid())
            new_line.set_ls(old_line.get_ls())
            new_line.set_lw(old_line.get_lw())
            new_line.set_color(old_line.get_color())
            new_line.set_marker(old_line.get_marker())
            new_line.set_markersize(old_line.get_markersize())
            new_line.set_markerfacecolor(old_line.get_markerfacecolor())
            new_line.set_markeredgewidth(old_line.get_markeredgewidth())
            new_line.set_markeredgecolor(old_line.get_markeredgecolor())
        if delete:
            old_line.remove()
        self.line_moved.emit()
        self.update_legend()

    def contextmenu(self,point):
        menu = QMenu(self)
        duplicate_action = menu.addAction('Duplicate')
        duplicate_action.triggered.connect(self.duplicate)
        delete_action = menu.addAction('Delete')
        delete_action.triggered.connect(self.delete)
        menu.exec_(self.mapToGlobal(point))

    def duplicate(self):
        irow = self.currentRow()
        line = self.lines[irow]
        self.gui_call("move_line", line, line.axes, delete=False)
        self.update_legend()
        line.axes.figure.canvas.draw()
        self.load_lines()

    def delete(self):
        irow = self.currentRow()
        line = self.lines[irow]
        fig = line.axes.figure
        self.gui_call("move_line", line, None, delete=True)
        fig.canvas.draw()
        self.load_lines()

    def move_by_drag(self, alias, ax, is_copy):
        s = re.split("fig|ax|l", alias)
        line = self.figs[int(s[1])].axes[int(s[2])].lines[int(s[3])]
        self.gui_call("move_line", line, ax, delete = not is_copy)
        self.figs[int(s[1])].canvas.draw()
        ax.figure.canvas.draw()
        self.load_lines()

    def on_pick(self, e):
        if self._line_draggable:
            line = e.artist
            self.aliasbuttons[line].mouseMoveEvent(e.guiEvent)

    # def closeEvent(self, a0: QCloseEvent) -> None:
    #     self.initialize()
    #     return super().closeEvent(a0)
    
    def show(self):
        super().show()
        self.load_lines()


class AxesTool(BaseTool):
    def __init__(self, figs, fixsize = True):
        header = ["figs","axes","title","xlabel","ylabel","xmin","xmax","xscale","ymin","ymax","yscale"]
        title = "AxesTool"
        super().__init__(figs, None, header, title, fixsize)
        self.load_axes()
        self.horizontalHeader().sectionClicked.connect(self.allset)

    def allset(self, column):
        # show context menu
        if self.header[column] in ['figs', 'axes']: return
        menu = QMenu(self)
        allset_action = menu.addAction('Copy 1 to all')
        allset_action.triggered.connect(lambda: self._allset(column))
        menu.exec_(QCursor.pos())

    def appendCellWidgetToColumn(self,type,initial=None,dict=None,max=None,readonly=False):
        obj = super().appendCellWidgetToColumn(type,initial,dict,max,readonly)
        if type == "float":
            obj.setFixedWidth(60)
        elif type == "str":
            obj.setFixedWidth(150)
        return obj
        
    def load_axes(self):
        self.initialize()
        for h, fig in enumerate(self.figs):
            for i, ax in enumerate(fig.axes):
                self.appendRow()
                # figs
                self.appendCellWidgetToColumn("int", initial=h, readonly=True)
                # axes
                self.appendCellWidgetToColumn("int", initial=i, readonly=True)
                # title
                self.appendCellWidgetToColumn("str", initial=ax.get_title())
                # xlabel
                self.appendCellWidgetToColumn("str", initial=ax.get_xlabel())
                # ylabel
                self.appendCellWidgetToColumn("str", initial=ax.get_ylabel())
                # xmin
                self.appendCellWidgetToColumn("float", initial=ax.get_xlim()[0])
                # xmax
                self.appendCellWidgetToColumn("float", initial=ax.get_xlim()[1])
                # xscale
                self.appendCellWidgetToColumn("combo", initial=ax.get_xscale(), dict={"linear":"linear","log":"log"})
                # ymin
                self.appendCellWidgetToColumn("float", initial=ax.get_ylim()[0])
                # ymax
                self.appendCellWidgetToColumn("float", initial=ax.get_ylim()[1])
                # yscale
                self.appendCellWidgetToColumn("combo", initial=ax.get_yscale(), dict={"linear":"linear","log":"log"})
        self.resizeColumnsToContents()
        self.fit_size()

    def quick_set_own(self, row, col):
        figid = self.cellWidget(row,0).value()
        axid = self.cellWidget(row,1).value()
        ax = self.figs[figid].axes[axid]
        data = [
            ax.get_title(),
            ax.get_xlabel(),
            ax.get_ylabel(),
            ax.get_xlim()[0],
            ax.get_xlim()[1],
            ax.get_xscale(),
            ax.get_ylim()[0],
            ax.get_ylim()[1],
            ax.get_yscale()
        ]
        for i, d in enumerate(data):
            if i == col - 2: continue
            self.cellWidget(row,i+2).set(d)

    def quick_set_others(self, called_row, called_col):
        for irow in range(self.rowCount()):
            if irow == called_row: continue
            self.quick_set_own(irow, -1)

    def _update(self, irow, jcol):
        values = {h:self.cellWidget(irow,icol).value() for icol, h in enumerate(self.header)}
        if values["xmin"] <= 0 and values["xscale"] == "log":
            values["xmin"] = 1e-6
        if values["ymin"] <= 0 and values["yscale"] == "log":
            values["ymin"] = 1e-6
        if values["xmax"] <= 0 and values["xscale"] == "log":
            values["xmax"] = 1.0
        if values["ymax"] <= 0 and values["yscale"] == "log":
            values["ymax"] = 1.0
        if values["xmin"] == values["xmax"] or values["ymin"] == values["ymax"]:
            return
        try:
            self.gui_call("set_axesproperties", values)
            self.figs[values["figs"]].canvas.draw()
        except:
            pass
        self.quick_set_own(irow, jcol)

    def update(self):
        super().update()
        self.quick_set_others(self.sender().row, self.sender().column)

    def show(self):
        super().show()
        self.load_axes()

    def set_axesproperties(self, values):
        ax = self.figs[values["figs"]].axes[values["axes"]]
        ax.set_title(values["title"])
        ax.set_xlabel(values["xlabel"])
        ax.set_xlim((values["xmin"],values["xmax"]))
        ax.set_xscale(values["xscale"])
        ax.set_ylabel(values["ylabel"])
        ax.set_ylim((values["ymin"],values["ymax"]))
        ax.set_yscale(values["yscale"])
