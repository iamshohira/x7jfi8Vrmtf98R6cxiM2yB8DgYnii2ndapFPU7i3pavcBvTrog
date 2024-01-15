import sys,os,pickle
import glob
import numpy as np
from datetime import datetime
import subprocess
import shutil
import argparse
import graphlib
import matplotlib
from matplotlib import font_manager
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from JEMViewer2.ipython_widget import IPythonWidget
from JEMViewer2.figure_widget import MyFigureCanvas, DDHandler, randomname, MyToolbar
from JEMViewer2.log_widget import LogWidget
from JEMViewer2.edit_widget import EditWidget, TempWidget
from JEMViewer2.file_handler import savefile, envs
from JEMViewer2.addon_installer import AddonInstaller
from JEMViewer2.axeslinestool import AxesTool, LinesTool
from JEMViewer2.auto_update import AutoUpdater
from JEMViewer2.notion_handler import NotionHandler
import webbrowser

if os.name == "nt": #windows
    import PyQt6
    dirname = os.path.dirname(PyQt6.__file__)
    plugin_path = os.path.join(dirname, "Qt6", "plugins", "platforms")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

floatstyle = "Floating style"
dockstyle = "Docking style"
modes = [floatstyle, dockstyle]
mode = floatstyle

parser = argparse.ArgumentParser()
parser.add_argument("filename", nargs='?', default=None, help="input filename")
parser.add_argument("-l","--local", action="store_true")
parser.add_argument("-u","--update", default=None, help="force update to the specified version")
args = parser.parse_args()
envs.initialize(args)
savefile.set_workspace(envs.TEMP_DIR)
DEFAULT_NAMESPACE = {
    "np": np,
    "pickle": pickle,
    "os": os,
}

EXIT_CODE_REBOOT = -11231351
ipaexg = os.path.join(envs.RES_DIR, "ipaexg.ttf")
ipaexm = os.path.join(envs.RES_DIR, "ipaexm.ttf")

class BaseMainWindow(QMainWindow):
    def __init__(self, filepath, reboot=True, widgets=None, call_as_library = False, call_from = None, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._set_statusbar()
        self.force_close = False
        self.call_as_library = call_as_library
        self.call_from = call_from
        self.notion_handler = NotionHandler(envs.SETTING_DIR)
        self.auto_updater = AutoUpdater(self.notion_handler)
        self._create_menubar()
        self.saved_command = ""
        self.window_id = randomname(4)
        self.setWindowTitle(f"JEMViewer2 id: {self.window_id}")
        self.filepath = filepath
        if filepath != None:
            matplotlib.rcParams['savefig.directory'] = (os.path.dirname(filepath))
        self.toolbar = MyToolbar(self, self.is_floatmode)
        self._load_font()
        self._set_update_timer()        
        if reboot:
            header = self.auto_updater.header if not call_as_library else "JEMViewer2 as Python Library\n\n"
            self.ipython_w = IPythonWidget(header)
            self.log_w = LogWidget(self)
            self.figs = []
        else:
            self.ipython_w = widgets["ipython"]
            self.log_w = widgets["log"]
            self.figs = widgets["figures"]
        self.figure_widgets = []
        self.ns = self.ipython_w.ns
        self.linestool = LinesTool(self.figs, self.ns, self.is_floatmode)
        self.axestool = AxesTool(self.figs, self.is_floatmode)
        self._create_main_window()
        self._set_slot()
        if reboot:
            self.add_figure()
        else:
            for fig in self.figs:
                self.add_figure(fig)
        self.initialize(reboot)

    def _set_statusbar(self):
        # set for loc rabel of mpltoolbar
        self.bar = self.statusBar()
        self.bar.setText = self.bar.showMessage
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setFixedWidth(100)
        self.slider.setRange(10,50)
        self.slider.setValue(10)
        self.text = QLabel("100%")
        self.text.setFixedWidth(40)
        self.bar.addPermanentWidget(self.slider)
        self.bar.addPermanentWidget(self.text)
        self.slider.valueChanged.connect(lambda x: self.text.setText(f"{10*x}%"))
        self.slider.valueChanged.connect(lambda x: self.magnify_figures(10*x))

    def magnify_figures(self, value):
        for figure_w in self.figure_widgets:
            figure_w.magnify(value)

    def _load_font(self):
        # avoid overwriting error for font files when updating
        if self.call_as_library or not self.auto_updater.can_update:
            font_manager.fontManager.addfont(ipaexg)
            font_manager.fontManager.addfont(ipaexm)

    def _set_update_timer(self):
        if not self.call_as_library:
            if self.auto_updater.can_update or args.update != None:
                self.timer_for_update = QTimer(self)
                def do_update():
                    self.auto_updater.update(args.update)
                    self.close_(True)
                    self.timer_for_update.stop()
                self.timer_for_update.timeout.connect(do_update)
                self.timer_for_update.start(1000)

    def _create_menubar(self):
        menubar = self.menuBar()
        filemenu = menubar.addMenu("&File")
        save = QAction( "&Save",self)
        save.setShortcut(QKeySequence.Save)
        save.triggered.connect(self.save)
        filemenu.addAction(save)
        saveas = QAction("Save &As",self)
        saveas.setShortcut(QKeySequence.SaveAs)
        saveas.triggered.connect(self.saveas)
        filemenu.addAction(saveas)
        open_ = QAction("&Open",self)
        open_.setShortcut(QKeySequence.Open)
        open_.triggered.connect(self.open)
        filemenu.addAction(open_)
        
    def print_log(self,item):
        self.ipython_w.clearPrompt()
        self.ipython_w.printTextInBuffer(item.text())

    def print_log_str(self, text):
        self.ipython_w.clearPrompt()
        self.ipython_w.printTextInBuffer(text)

    def dragEnterEvent(self,event):
        event.accept()

    def dropEvent(self,event):
        if event.mimeData().hasUrls():
            event.accept()
            for url in event.mimeData().urls():
                if url.path().endswith(".jem2"):
                    self.filepath = url.path()
                    self.reboot()
        else:
            event.ignore()
        
    def _load_helper(self):
        with open(os.path.join(envs.EXE_DIR,'helper_function.py'), 'r') as f:
            command = f.read()
            if command not in self.saved_command:
                self.ipython_w.executeCommand(command,hidden=True)
                # savefile.save_command(command, alias=False)

    def _load_user_py(self):
        files = glob.glob(os.path.join(envs.ADDON_DIR,"*.py"))
        dependences = {}
        for fi in files:
            with open(fi, "r", encoding='utf-8') as f:
                f.readline()
                line = f.readline()
                if "Dependence:" in line:
                    dep = [i.strip() for i in line.split(":")[1].split(",")]
                else:
                    dep = [""]
            dependences[os.path.basename(fi)] = dep
        ts = graphlib.TopologicalSorter(dependences)
        for fn in ts.static_order():
            if fn == "": continue
            fi = os.path.join(envs.ADDON_DIR, fn)
            with open(fi,'r', encoding='utf-8') as f:
                command = f.read()
                if command not in self.saved_command:
                    self.ipython_w.executeCommand(command,hidden=True)
                    savefile.save_command(command, alias=False, exclude=[])
        self.ipython_w.executeCommand("",hidden=True)

    def open_manual(self):
        if self.notion_handler.ok:
            webbrowser.open_new(self.notion_handler.data["manual_url"])

    def close_(self, force):
        self.force_close = force
        self.close()

    def closeEvent(self, event):
        def exit():
            for figure_w in self.figure_widgets:
                figure_w.close_()
            self.linestool.close()
            self.axestool.close()
            event.accept()

        if self.force_close:
            exit()
            return            
        if '*' not in self.windowTitle():
            exit()
            return
        reply = QMessageBox.question(self,'Exit',
                                     "Do you want to save your changes?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                     QMessageBox.Save)
        if reply == QMessageBox.Discard:
            exit()
        elif reply == QMessageBox.Save:
            self.save()
            exit()
        else:
            event.ignore()    

    def draw_and_requiring_save(self):
        for figure_w in self.figure_widgets:
            figure_w.draw()
        title = self.windowTitle()
        if '*' not in title:
            self.setWindowTitle(title+'*')

    def _set_slot(self):
        self.linestool.line_moved.connect(self.update_alias)
        self.linestool.alias_clicked.connect(self.ipython_w.printTextAtCurrentPos)
        self.ipython_w.command_finished.connect(self.log_w.store)
        self.ipython_w.command_finished.connect(self._save_command_with_parse)
        self.log_w.item_added.connect(self.draw_and_requiring_save)
        self.log_w.itemDoubleClicked.connect(self.print_log)
        self.log_w.inputText.connect(self.print_log_str)
        self.ipython_w.command_finished.connect(self.update_alias)

    def add_figure(self, fig=None):
        figure_w = MyFigureCanvas(self, self.toolbar, self.call_as_library, self.call_from, fig=fig)
        figure_w.set_window_title(id=len(self.figure_widgets), prefix=self.window_id)
        figure_w.nd_pasted.connect(self.append_ndarray)
        figure_w.line_pasted.connect(self.append_line2D)
        figure_w.table_required.connect(self.open_tablewidget)
        figure_w.custom_loader.connect(self.run_custom_loader)
        figure_w.nd_pasted.connect(self.update_alias)
        figure_w.line_pasted.connect(self.update_alias)
        figure_w.table_required.connect(self.update_alias)
        figure_w.custom_loader.connect(self.update_alias)
        figure_w.alias_pasted.connect(self.linestool.move_by_drag)
        figure_w.remove_required.connect(self.remove_figure)
        self.show_widget(figure_w)
        self.toolbar.add_canvas(figure_w)
        self.figure_widgets.append(figure_w)
        if fig is None:
            self.figs.append(figure_w.fig)
        self.update_alias()
        return figure_w.fig

    def remove_figure(self, id):
        figure_w = self.figure_widgets.pop(id)
        figs = self.figs.pop(id)
        self.toolbar.remove_canvas(figure_w)
        figure_w.nd_pasted.disconnect(self.append_ndarray)
        figure_w.line_pasted.disconnect(self.append_line2D)
        figure_w.table_required.disconnect(self.open_tablewidget)
        figure_w.custom_loader.disconnect(self.run_custom_loader)
        figure_w.nd_pasted.disconnect(self.update_alias)
        figure_w.line_pasted.disconnect(self.update_alias)
        figure_w.table_required.disconnect(self.update_alias)
        figure_w.custom_loader.disconnect(self.update_alias)
        figure_w.alias_pasted.disconnect(self.linestool.move_by_drag)
        figure_w.remove_required.disconnect(self.remove_figure)
        figure_w.close_()
        for i, figure_w in enumerate(self.figure_widgets):
            figure_w.set_window_title(id=i)
        self.update_alias()
        return figure_w
            
    def _remove_slot(self):
        self.linestool.line_moved.disconnect(self.update_alias)
        self.linestool.alias_clicked.disconnect(self.ipython_w.printTextAtCurrentPos)
        self.ipython_w.command_finished.disconnect(self.log_w.store)
        self.ipython_w.command_finished.disconnect(self._save_command_with_parse)
        self.log_w.item_added.disconnect(self.draw_and_requiring_save)
        self.log_w.itemDoubleClicked.disconnect(self.print_log)
        self.log_w.inputText.disconnect(self.print_log_str)
        self.ipython_w.command_finished.disconnect(self.update_alias)

    @pyqtSlot(str,np.ndarray)
    def append_ndarray(self,key,value):
        self.ns[key] = value
        self.ns["justnow"] = value
        text  = "# New ndarray was generated\n"
        text += "# Name: {}\n".format(key,)
        text += "# Size: {}".format(value.shape,)
        self.log_w.add_item(text)

    @pyqtSlot(str,list)
    def append_line2D(self,key,value):
        if len(value) == 1:
            self.ns[key] = value[0]
            self.ns["justnow"] = value[0]
            text  = "# New plot was generated\n"
            text += "# Name: {}".format(key,)
        else:
            self.ns[key] = value
            self.ns["justnow"] = value
            text  = "# New plot list was generated\n"
            text += "# Name: {}\n".format(key,)
            text += "# Size: {}".format(len(value))
        self.log_w.add_item(text)

    def save(self):
        if self.filepath is None:
            self.saveas()
            return
        self._save()

    def _save(self):
        self._set_windowname()
        log = self.log_w.get()
        savefile.save_log(log)
        savefile.save(self.filepath)
        
    def saveas(self):
        path = self.filepath if self.filepath is not None else os.path.join(os.path.expanduser('~'),'Desktop')
        filepath = QFileDialog.getSaveFileName(self,"Project name",path,"JEM Viewer 2 file (*.jem2)")
        if filepath[0] == '':
            return
        self.filepath = filepath[0]
        matplotlib.rcParams['savefig.directory'] = (os.path.dirname(self.filepath))
        self._save()

    def open(self):
        # path = self.filepath if self.filepath is not None else os.path.join(os.path.expanduser('~'),'Desktop')
        filepath = QFileDialog.getOpenFileName(self,"Project name",self.filepath,"JEM Viewer 2 file (*.jem2)")
        if filepath[0] == '':
            return
        self.filepath = filepath[0]
        self.reboot()

    # def reboot(self,force=False):
    #     for figure_w in self.figure_widgets:
    #         figure_w.close_()
    #     self.ipython_w.stop()
    #     self.close_(force)
    #     get_app_qt6().exit(EXIT_CODE_REBOOT)

    def _set_windowname(self):
        self.setWindowTitle(os.path.basename(self.filepath))
        for i, figure_w in enumerate(self.figure_widgets):
            figure_w.set_window_title(i, prefix=os.path.basename(self.filepath))
            figure_w.get_default_filename = lambda: f"{os.path.splitext(self.filepath)[0]}.{figure_w.get_default_filetype()}"

    def _load_savefile(self):
        if self.filepath != None:
            savefile.open(self.filepath)
            command = savefile.load()
            # PyQt5 to PyQt6
            command = command.replace("PyQt5","PyQt6")
            log = savefile.load_log()
            self._set_windowname()
            self.log_w.set(log)
            self.saved_command = command
            self.ipython_w.executeCommand(command,hidden=True)

    def show_datatable(self, data):
        if type(data) == Line2D:
            data = np.vstack(data.get_data())
        self.editwidget = EditWidget(data.T)
        self.show_widget(self.editwidget)
    
    @pyqtSlot(str,str)
    def open_tablewidget(self,filename,sep):
        self.tempwidget = TempWidget(filename,sep)
        self.tempwidget.setGeometry(self.geometry().left(),self.geometry().top(),self.geometry().width(),self.geometry().height())
        self.show_widget(self.tempwidget)

    @pyqtSlot(list)
    def run_custom_loader(self,lis):
        functionname = lis[0]
        filename = lis[1]
        inaxes = lis[2]
        newname = lis[3]
        try:
            self.ns[newname] = self.ns[functionname](filename,inaxes)
            self.ns["justnow"] = self.ns[newname]
            text  = "# Output from \"{}\" was generated\n".format(functionname,)
            text += "# Name: {}\n".format(newname,)
            self.log_w.add_item(text)
            # self.figure_w.draw()
            savefile.save_customloader(lis)
        except Exception as e:
            message = f"type:{str(type(e))}\nargs:{str(e.args)}\n\n{str(e)}"
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Icon.Critical)
            msgBox.setText(f"Load Error\n{functionname} does not exist or there is something wrong with this function.")
            msgBox.setDetailedText(message)
            msgBox.exec()

    def execom(self,command):
        self.ipython_w.executeCommand(command)
        savefile.save_command(command, alias=False, exclude=[])
        
    def _set_initial_namespace(self):
        namespace = {
            #"ax": self.figure_widgets[0].fig.axes[0],
            "fig_widget": self.figure_widgets[0],
            "fig_widgets": self.figure_widgets,
            "edit": self.direct_edit,
            "set_loader": DDHandler.set_loader,
            "savedir": savefile.dirname,
            "reboot": self.reboot,
            "update_alias": self.update_alias,
            "show_data": self.show_datatable,
            "add_figure": self.add_figure,
            "remove_figure": self.remove_figure,
            "addon_store": AddonInstaller(envs.ADDON_DIR, self.notion_handler),
            "set_lineproperties": self.linestool.set_lineproperties,
            "move_line": self.linestool.move_line,
            "update_legend": self.linestool.update_legend,
            "set_axesproperties": self.axestool.set_axesproperties,
            "legend_autoupdate": self.linestool.legend_autoupdate,
            "notion_handler": self.notion_handler,
            "reload_addon": self._load_user_py,
            "execom": self.execom,
            "get_log": self.log_w.get,
            "ipy": self.ipython_w,
            "save_history": self.ipython_w.saveHistory,
            "dockmode": self.dockmode,
            "floatmode": self.floatmode,
            "is_floatmode": self.is_floatmode,
        }
        self.ns.update(DEFAULT_NAMESPACE)
        self.ns.update(namespace)

    def _save_command(self,fileparse=False):
        if self.ipython_w.error:
            return
        id_ = len(self.ns['In'])-1
        lastcommand = self.ns['In'][-1].strip()
        if id_ in self.ns['Out']:
            lastcommand = "_ = " + lastcommand
        savefile.save_command(lastcommand,fileparse)

    def _save_command_with_parse(self):
        self._save_command(True)

    def initialize(self, reboot):
        savefile.set_figure(self.figs)
        self._set_initial_namespace()
        self.update_alias() 
        if reboot:
            self._load_helper()
            self._load_savefile()
            savefile.save_command(datetime.now().strftime('\n# HEADER %Y-%m-%d %H:%M:%S\n'),alias=False)
            self._load_user_py()
            savefile.save_command(datetime.now().strftime('\n# COMMAND LOG %Y-%m-%d %H:%M:%S\n'),alias=False)
            self.update_alias()

    def direct_edit(self):
        subprocess.run([envs.RUN, savefile.logfilename])

    def update_alias(self):
        alias = {}
        alias["figs"] = self.figs
        for i, fig in enumerate(self.figs):
            alias[f"fig{i}"] = fig
            alias[f"fig{i}axs"] = fig.axes
            for j, ax in enumerate(fig.axes):
                if j == 0:
                    alias[f"fig{i}ax"] = ax
                alias[f"fig{i}ax{j}"] = ax
                alias[f"fig{i}ax{j}ls"] = ax.lines
                for k, line in enumerate(ax.lines):
                    alias[f"fig{i}ax{j}l{k}"] = line
                    alias[f"fig{i}ax{j}l{k}x"] = line.get_xdata()
                    alias[f"fig{i}ax{j}l{k}y"] = line.get_ydata()
                    alias[f"fal{i}{j}{k}"] = line
                    alias[f"fal{i}{j}{k}x"] = line.get_xdata()
                    alias[f"fal{i}{j}{k}y"] = line.get_ydata()
        if len(self.figs) > 0:
            alias["fig"] = self.figs[0]
            alias["axs"] = self.figs[0].axes
            for ia, ax in enumerate(self.figs[0].axes):
                alias["ax{}".format(ia,)] = ax
                alias["ax{}ls".format(ia,)] = ax.lines
                for il, line in enumerate(ax.lines):
                    alias["ax{}l{}".format(ia,il)] = line
                    alias["ax{}l{}x".format(ia,il)] = line.get_xdata()
                    alias["ax{}l{}y".format(ia,il)] = line.get_ydata()
            if len(self.figs[0].axes) > 0:
                alias["ax"] = self.figs[0].axes[0]
                alias["ls"] = self.figs[0].axes[0].lines
                for il, line in enumerate(self.figs[0].axes[0].lines):
                    alias["l{}".format(il,)] = line
                    alias["l{}x".format(il,)] = line.get_xdata()
                    alias["l{}y".format(il,)] = line.get_ydata()
        self.ns.update(alias)
        self.linestool.load_lines()
        self.axestool.load_axes()

    def _switch_mode(self, MainWindowClass, reboot=False):
        self._remove_slot()
        widgets = {
            "ipython": self.ipython_w,
            "log": self.log_w,
            "figures": self.figs,
        }
        new = MainWindowClass(self.filepath, reboot=reboot, widgets=widgets, call_as_library=self.call_as_library, call_from=self.call_from)
        new.show()
        self.close_(True)

    def dockmode(self):
        self._switch_mode(DockMainWindow)

    def floatmode(self):
        self._switch_mode(FloatMainWindow)


class DockMainWindow(BaseMainWindow):
    def __init__(self, filepath, reboot=True, widgets=None, call_as_library = False, call_from = None, parent=None):
        self.is_floatmode = False
        self.mdiwindows = {}
        super().__init__(filepath, reboot, widgets, call_as_library, call_from, parent)
        self._create_sortmenubar()

    def reboot(self):
        self._switch_mode(DockMainWindow, reboot=True)

    def switch_mode(self):
        self._switch_mode(FloatMainWindow)

    def _create_sortmenubar(self):
        sortmenu = self.menuBar().addMenu("&Sort")
        sortmenu.addAction("Cascade")
        sortmenu.addAction("Tile")
        def mdiaction(q):
            if q.text() == "Cascade":
                self.mdi.cascadeSubWindows()
            if q.text() == "Tile":
                self.mdi.tileSubWindows()
        sortmenu.triggered[QAction].connect(mdiaction)

    def _create_main_window(self):
        self.mdi = QMdiArea(self)
        self.mdi.setActivationOrder(QMdiArea.WindowOrder.StackingOrder)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar)
        self.add_essential_dock("console", self.ipython_w, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.add_essential_dock("log", self.log_w, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.add_essential_dock("axestool",self.axestool, Qt.DockWidgetArea.BottomDockWidgetArea)
        self.add_essential_dock("linestool",self.linestool, Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setCentralWidget(self.mdi)

    def add_essential_dock(self, title, wid, pos):
        dock = QDockWidget(title, self)
        dock.setWidget(wid)
        self.addDockWidget(pos, dock)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable )
        return dock
    
    def add_dock(self, wid, title="", pos="right"):
        posdic = {
            "top": Qt.DockWidgetArea.TopDockWidgetArea,
            "left": Qt.DockWidgetArea.LeftDockWidgetArea,
            "right": Qt.DockWidgetArea.RightDockWidgetArea,
            "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
        }
        dock = QDockWidget(title, self)
        dock.setWidget(wid)
        self.addDockWidget(posdic[pos], dock)

    def show_widget(self, widget, title=None):
        sub = QMdiSubWindow()
        sub.setWidget(widget)
        #sub.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        self.mdi.addSubWindow(sub)
        sub.show()
        self.mdiwindows[widget] = sub
        if title != None:
            sub.setWindowTitle(title)

    def remove_figure(self, id):
        figure_w = super().remove_figure(id)
        self.mdi.removeSubWindow(self.mdiwindows[figure_w])

    def tiling(self):
        self.mdi.tileSubWindows()

    def cascading(self):
        self.mdi.cascadeSubWindows()

    def _set_initial_namespace(self):
        super()._set_initial_namespace()
        additionalnamespace = {
            "add_dock": self.add_dock,
            "add_mdi": self.show_widget,
            "tiling_windows": self.tiling,
            "cascading_windows": self.cascading,
            "notion_handler": self.notion_handler,
            "mdiwindows": self.mdiwindows,
        }
        self.ns.update(additionalnamespace)

    def add_figure(self, fig=None):
        fig_ = super().add_figure(fig)
        fig_.canvas.set_mdi(self.mdiwindows[fig_.canvas])
        return fig_


class FloatMainWindow(BaseMainWindow):
    def __init__(self, filepath, reboot=True, widgets=None, call_as_library = False, call_from = None, parent=None):
        self.is_floatmode = True
        super().__init__(filepath, reboot, widgets, call_as_library, call_from, parent)
        self.setGeometry(300, 300, 850, 500)
        self._create_main_window()

    def reboot(self):
        self._switch_mode(FloatMainWindow, reboot=True)

    def switch_mode(self):
        self._switch_mode(DockMainWindow)

    def _create_main_window(self):
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.splitter = QSplitter()
        self.log_w.resize(250,250)
        self.splitter.addWidget(self.log_w)
        self.splitter.addWidget(self.ipython_w)
        self.setCentralWidget(self.splitter)

    def raise_figure_widgets(self):
        for figure_w in self.figure_widgets:
            figure_w.raise_()

    def show_widget(self, widget):
        widget.show()

    def _set_initial_namespace(self):
        super()._set_initial_namespace()
        additionalnamespace = {
            "popup": self.raise_figure_widgets,
        }
        self.ns.update(additionalnamespace)


def get_app_qt6(*args, **kwargs):
    """Create a new qt6 app or return an existing one."""
    app = QApplication.instance()
    if app is None:
        if not args:
            args = ([''],)
        app = QApplication(*args, **kwargs)
    return app

def main():
    filename = args.filename
    os.makedirs(envs.JEMDIR, exist_ok=True)
    os.makedirs(envs.TEMP_DIR, exist_ok=True)
    if not os.path.exists(envs.ADDON_DIR):
        shutil.copytree(envs.ADDON_TEMPRATE_DIR, envs.ADDON_DIR)
    if not os.path.exists(envs.SETTING_DIR):
        shutil.copytree(envs.SETTING_TEMPRATE_DIR, envs.SETTING_DIR)
    plt.style.use(envs.PLTPLOFILE)

    app = QApplication([])
    mainwindow = FloatMainWindow(filename)
    mainwindow.show()
    mainwindow.raise_()
    app.exec()
    # while True:
    #     app = get_app_qt6()
    #     app.setWindowIcon(QIcon(envs.LOGO))
    #     form = FloatMainWindow(filename)
    #     form.show()
    #     form.raise_()
    #     exit_code = app.exec_()
    #     filename = form.filepath
    #     del(form)
    #     del(app)
    #     if exit_code != EXIT_CODE_REBOOT:
    #         break
    savefile.remove_tmpdir()

if __name__ == "__main__":
    main()
    