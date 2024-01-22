import re
import os, json
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backend_bases import Event
import matplotlib.backends.qt_editor.figureoptions as figopt
from matplotlib import colors as mcolors
from JEMViewer2.file_handler import savefile, envs
import JEMViewer2.stylesheet as ss
from JEMViewer2.basetoolbar import BaseToolbar
from matplotlib.text import Text
from JEMViewer2.fontdialog import FontDialog
from matplotlib.legend import Legend, DraggableLegend

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
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.figs = figs
        self.ns = ns
        self.setWindowTitle(title)
        # change header text color to red if selected
        self.verticalHeader().setStyleSheet(ss.headerview)
        self.setStyleSheet(ss.tablewidget)

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


class MyLegend(Legend):
    def set_draggable(self, state, use_blit=False, update='loc'):
        if state:
            if self._draggable is None:
                self._draggable = MyDraggableLegend(self, use_blit=use_blit, update=update)
        else:
            if self._draggable is not None:
                self._draggable.disconnect()
            self._draggable = None
        return self._draggable
    
class MyDraggableLegend(DraggableLegend):
    def finalize_offset(self):
        super().finalize_offset()
        self.gui_call("set_legend_loc", self.legend.axes, self.legend._loc)

    @classmethod
    def set_legend_loc(cls, axes, loc):
        if type(axes) == dict:
            axes = savefile.dict_to_mpl(axes)
        if axes.legend_ != None:
            axes.legend_._loc = loc
            axes.figure.canvas.draw()

    def gui_call(self, function_name, *args, **kwargs):
        savefile.save_emulate_command(function_name, *args, **kwargs)
        f = getattr(self, function_name)
        f(*args, **kwargs)


class LinesToolbar(BaseToolbar):
    def __init__(self, figs, parent=None):
        self.table = parent.table
        self.toolitems = (
            ("EnableLineDrag", "Enable line drag", os.path.join(envs.RES_DIR,'linedrag'), 'enable_line_drag', None, True),
            ('AutoLegend', 'Auto legend mode', os.path.join(envs.RES_DIR,'auto'), 'auto_legend', None, True),
            ('Clone', 'Clone selected texts', os.path.join(envs.RES_DIR,'clone'), 'clone', None, False),
            ('Remove', 'Remove selected texts', os.path.join(envs.RES_DIR,'trash'), 'remove', None, False),
        )
        super().__init__(parent)

    def trigger_legend_update(self, b):
        self.actions['auto_legend'].setChecked(b)

    def auto_legend(self):
        self.table.set_legend_autoupdate(self.actions['auto_legend'].isChecked())
        savefile.save_emulate_command("set_legend_autoupdate", self.actions['auto_legend'].isChecked())

    def enable_line_drag(self):
        self.table.set_line_draggable(self.actions['enable_line_drag'].isChecked())

    def remove(self):
        self.table.delete()

    def clone(self):
        self.table.duplicate()
    

class LinesTool(QMainWindow):
    def __init__(self, figs, ns, fix_size=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LinesTool")
        self.table = LinesTable(figs, ns, self, fix_size)
        self.line_moved = self.table.line_moved
        self.alias_clicked = self.table.alias_clicked
        self.toolbar = LinesToolbar(figs, self)
        self.table.legend_update_called.connect(self.toolbar.trigger_legend_update)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setStyleSheet(ss.toolbutton)
        self.toolbar.setIconSize(QSize(20,20))
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar)
        self.setCentralWidget(self.table)

    def set_lineproperties(self, line, values):
        self.table.set_lineproperties(line, values)

    def move_line(self, old_line, new_axes, delete=True):
        self.table.move_line(old_line, new_axes, delete)

    def update_legend(self):
        self.table.update_legend()

    def set_legend_autoupdate(self, b):
        self.table.set_legend_autoupdate(b)

    def move_by_drag(self, alias, ax, is_copy):
        self.table.move_by_drag(alias, ax, is_copy)

    def load_lines(self):
        self.table.load_lines()

    def show(self):
        super().show()
        self.load_lines()


class LinesTable(BaseTool):
    line_moved = pyqtSignal()
    alias_clicked = pyqtSignal(str)
    legend_update_called = pyqtSignal(bool)
    def __init__(self, figs, ns, parent, fixsize = True):
        header = ["show","alias","zorder","legend","label","memo","line style","width","line color","marker","size","marker color","edge","edge color"]
        title = "LinesTool"
        self.parent = parent
        super().__init__(figs, ns, header, title, fixsize)
        self.cids = {}
        self._line_draggable = False
        self.load_lines()
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.contextmenu)
        self.horizontalHeader().sectionClicked.connect(self.allset)

    def fit_size(self):
        if self.fixsize:
            self.parent.setMinimumWidth(self.horizontalHeader().length()+40+20)
            self.parent.setMaximumWidth(self.horizontalHeader().length()+40+20)
            self.parent.setMinimumWidth(100)
            height = self.verticalHeader().length()+40
            height = height if height > 180 else 180
            height = height if height < 400 else 400
            self.parent.setMinimumHeight(height)
            self.parent.setMaximumHeight(self.verticalHeader().length()+40)
            self.parent.setMinimumWidth(100)

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

    def set_legend_autoupdate(self, b):
        self._legend_autoupdate = b
        if b:
            self.update_legend()
        self.legend_update_called.emit(b)

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
                    # visible
                    # attribute check
                    if hasattr(line, "visible_in_legend"):
                        b = line.visible_in_legend
                    else:
                        b = False
                    self.appendCellWidgetToColumn("bool", initial=b)
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
        if "legend" in values.keys():
            line.visible_in_legend = values["legend"]
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
                handles = []
                labels = []
                for line in ax.lines:
                    if hasattr(line, "visible_in_legend"):
                        if line.visible_in_legend:
                            handles.append(line)
                            labels.append(line.get_label())
                if (ol := ax.legend_) != None:
                    loc = ol._loc
                    ol.set_draggable(False)
                else:
                    loc = 'best'
                ax.legend_ = MyLegend(ax, handles, labels, loc=loc, draggable=True)
            fig.canvas.draw()
                # nl._set_loc(loc)
                # nl.set_draggable(drag)

    def move_line(self, old_line, new_axes, delete=True):
        if type(old_line) == dict:
            old_line = savefile.dict_to_mpl(old_line)
        if new_axes != None:
            if type(new_axes) == dict:
                new_axes = savefile.dict_to_mpl(new_axes)
            new_line, = new_axes.plot(*old_line.get_data())
            new_line.set_visible(old_line.get_visible())
            new_line.set_zorder(old_line.get_zorder())
            if hasattr(old_line, "visible_in_legend"):
                new_line.visible_in_legend = old_line.visible_in_legend
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

    # def contextmenu(self,point):
    #     menu = QMenu(self)
    #     duplicate_action = menu.addAction('Duplicate')
    #     duplicate_action.triggered.connect(self.duplicate)
    #     delete_action = menu.addAction('Delete')
    #     delete_action.triggered.connect(self.delete)
    #     menu.exec_(self.mapToGlobal(point))

    def duplicate(self):
        lines = []
        for irow in self.selectedLows():
            lines.append(self.lines[irow])
        for line in lines:
            self.gui_call("move_line", line, line.axes, delete=False)
        self.update_legend()
        for fig in self.figs:
            fig.canvas.draw()
        self.load_lines()

    def delete(self):
        for irow in self.selectedLows()[::-1]:
            line = self.lines[irow]
            self.gui_call("move_line", line, None, delete=True)
        for fig in self.figs:
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


class TextsTable(BaseTool):
    va_choices = ["top","center_baseline","center","baseline","bottom"]
    ha_choices = ["left","center","right"]
    def __init__(self, figs, parent, fixsize = True):
        header = ["show","figs","text","x","y","va","ha","size","color","rotation"]
        title = "TextsTool"
        self.parent = parent
        super().__init__(figs, None, header, title, fixsize)
        self.load_texts()
        self.horizontalHeader().sectionClicked.connect(self.allset)

    def allset(self, column):
        # show context menu
        menu = QMenu(self)
        allset_action = menu.addAction('Copy 1 to all')
        allset_action.triggered.connect(lambda: self._allset(column))
        menu.exec_(QCursor.pos())

    def initialize(self):
        super().initialize()
        self.texts = []

    def figs_list(self):
        l = {}
        for i, fig in enumerate(self.figs):
            l[fig] = f"fig{i}"
        return l
        
    def load_texts(self):
        self.initialize()
        figs_list = self.figs_list()
        for h, fig in enumerate(self.figs):
            # self.cids[fig] = fig.canvas.mpl_connect('pick_event', self.on_pick)
            for j, text in enumerate(fig.texts):
                self.appendRow()
                # visible
                self.appendCellWidgetToColumn("bool", initial=text.get_visible())
                # figs
                self.appendCellWidgetToColumn("combo", initial=fig, dict=figs_list)
                # text
                self.appendCellWidgetToColumn("str", initial=text.get_text())
                x, y = text.get_position()
                # x
                self.appendCellWidgetToColumn("float", initial=x)
                # y
                self.appendCellWidgetToColumn("float", initial=y)
                # va
                self.appendCellWidgetToColumn("combo", initial=text.get_va(), dict={v:v for v in self.va_choices})
                # ha
                self.appendCellWidgetToColumn("combo", initial=text.get_ha(), dict={v:v for v in self.ha_choices})
                # size
                self.appendCellWidgetToColumn("float", initial=text.get_fontsize())
                # color
                color = mcolors.to_hex(mcolors.to_rgb(text.get_color()))
                self.appendCellWidgetToColumn("color", initial=color)
                # rotation
                self.appendCellWidgetToColumn("float", initial=text.get_rotation())
                self.texts.append(text)
        self.resizeColumnsToContents()
        self.fit_size()

    def _update(self, irow, _):
        values = {h:self.cellWidget(irow,icol).value() for icol, h in enumerate(self.header)}
        text = self.texts[irow]
        new_fig = values.pop("figs")
        self.gui_call("set_textproperties", text, values)
        old_fig = text.figure
        if old_fig != new_fig:
            self.gui_call("move_text", text, new_fig, delete=True)
            old_fig.canvas.draw()
        new_fig.canvas.draw()

    def set_textproperties(self, text, values):
        if type(text) == dict:
            text = savefile.dict_to_mpl(text)
        text.set_visible(values["show"])
        text.set_text(values["text"])
        text.set_position((values["x"], values["y"]))
        text.set_va(values["va"])
        text.set_ha(values["ha"])
        text.set_fontsize(values["size"])
        text.set_color(values["color"])
        text.set_rotation(values["rotation"])

    def move_text(self, old_text, new_fig, delete=True):
        if type(old_text) == dict:
            old_text = savefile.dict_to_mpl(old_text)
        if new_fig != None:
            if type(new_fig) == dict:
                new_fig = savefile.dict_to_mpl(new_fig)
            new_text = new_fig.text(*old_text.get_position(), old_text.get_text(), picker=True)
            new_text.set_visible(old_text.get_visible())
            new_text.set_zorder(old_text.get_zorder())
            new_text.set_va(old_text.get_va())
            new_text.set_ha(old_text.get_ha())
            new_text.set_fontsize(old_text.get_fontsize())
            new_text.set_color(old_text.get_color())
            new_text.set_rotation(old_text.get_rotation())
        if delete:
            old_text.remove()
        self.load_texts()

    def add_text(self, fig):
        if type(fig) == dict:
            fig = savefile.dict_to_mpl(fig)
        fig.text(0.5, 0.5, "new text", va='top', ha='left', picker=True)
        fig.canvas.draw()
        self.load_texts()

    def add(self):
        if len(self.figs) == 0: return
        self.gui_call("add_text", self.figs[0])

    def duplicate(self):
        texts = []
        for irow in self.selectedLows():
            texts.append(self.texts[irow])
        for text in texts:
            self.gui_call("move_text", text, text.figure, delete=False)
        for fig in self.figs:
            fig.canvas.draw()
        self.load_texts()

    def delete(self):
        for irow in self.selectedLows()[::-1]:
            text = self.texts[irow]
            self.gui_call("move_text", text, None, delete=True)
        for fig in self.figs:
            fig.canvas.draw()
        self.load_texts()

    def fit_size(self):
        if self.fixsize:
            self.parent.setMinimumWidth(self.horizontalHeader().length()+40+20)
            self.parent.setMaximumWidth(self.horizontalHeader().length()+40+20)
            self.parent.setMinimumWidth(100)
            height = self.verticalHeader().length()+40
            height = height if height > 210 else 210
            height = height if height < 400 else 400
            self.parent.setMinimumHeight(height)
            self.parent.setMaximumHeight(self.verticalHeader().length()+40)
            self.parent.setMinimumWidth(100)

    def refresh_and_save(self):
        self.load_texts()
        for irow in range(self.rowCount()):
            self._update(irow, -1)


class TextsToolbar(BaseToolbar):
    def __init__(self, figs, parent=None):
        self.table = parent.table
        FontDialog.set_figs(figs)
        self.ddhandler = DragHandler(figs)
        self.toolitems = (
            ('Add', 'Add new text', os.path.join(envs.RES_DIR,'addfigure'), 'add', None, False),
            ('Clone', 'Clone selected texts', os.path.join(envs.RES_DIR,'clone'), 'clone', None, False),
            ('Drag', 'Set texts draggable', os.path.join(envs.RES_DIR,'textdrag'), 'set_text_draggable', None, True),
            ('Refresh', 'Refresh texts', os.path.join(envs.RES_DIR,'refresh'), 'refresh_and_save', None, False),
            ('Remove', 'Remove selected texts', os.path.join(envs.RES_DIR,'trash'), 'remove', None, False),
            ('Font', 'Change font', os.path.join(envs.RES_DIR,'font'), 'font_setting', None, False),
        )
        super().__init__(parent)

    def font_setting(self):
        FontDialog.show()

    def add(self):
        self.table.add()

    def refresh_and_save(self):
        self.table.refresh_and_save()

    def set_text_draggable(self):
        self.ddhandler.set_draggable(self.actions["set_text_draggable"].isChecked())

    def remove(self):
        self.table.delete()

    def clone(self):
        self.table.duplicate()


class DragHandler:
    def __init__(self, figs):
        self.dragged = None
        self.cids = {}
        self.figs = figs

    def set_draggable(self, bool):
        if bool:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        self.cids = {}
        for fig in self.figs:
            self.cids[fig.canvas.mpl_connect("pick_event", self.on_pick_event)] = fig
            self.cids[fig.canvas.mpl_connect("motion_notify_event", self.on_motion_event)] = fig
            self.cids[fig.canvas.mpl_connect("button_release_event", self.on_release_event)] = fig

    def disconnect(self):
        for cid, fig in self.cids.items():
            fig.canvas.mpl_disconnect(cid)
    
    def on_pick_event(self, event):
        if isinstance(event.artist, Text):
            self.dragged = event.artist
            x0, y0 = self.dragged.get_position()
            self.pick_pos = (x0, y0, event.mouseevent.x, event.mouseevent.y)
        return True
    
    def on_motion_event(self, event):
        if self.dragged is not None:
            x0, y0, xpress, ypress = self.pick_pos
            w, h = self.dragged.figure.canvas.get_width_height()
            w *= self.dragged.figure.canvas.device_pixel_ratio
            h *= self.dragged.figure.canvas.device_pixel_ratio
            dx = event.x - xpress
            dy = event.y - ypress
            self.dragged.set_position((round(x0 + dx/w, 3), round(y0 + dy/h, 3)))
            self.dragged.figure.canvas.draw()

    def on_release_event(self, event):
        if self.dragged is not None:
            self.dragged.figure.canvas.draw()
            self.dragged = None
        return True
    

class TextsTool(QMainWindow):
    def __init__(self, figs, fix_size, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TextsTool")
        self.table = TextsTable(figs, self, fix_size)
        self.toolbar = TextsToolbar(figs, self)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setStyleSheet(ss.toolbutton)
        self.toolbar.setIconSize(QSize(20,20))
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar)
        self.setCentralWidget(self.table)

    def load_texts(self):
        self.table.load_texts()

    def show(self):
        super().show()
        self.load_texts()

    def set_textproperties(self, text, values):
        self.table.set_textproperties(text, values)

    def move_text(self, old_text, new_fig, delete=True):
        self.table.move_text(old_text, new_fig, delete)

    def add_text(self, fig):
        self.table.add_text(fig)



