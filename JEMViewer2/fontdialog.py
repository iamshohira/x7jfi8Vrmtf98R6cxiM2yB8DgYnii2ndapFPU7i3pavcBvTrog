from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib import font_manager
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
from JEMViewer2.file_handler import savefile, envs
import numpy as np


class LabeledComboBox(QComboBox):
    def __init__(self, label, items, initial=None, layout='horizontal'):
        super().__init__()
        self.layout = QHBoxLayout() if layout == 'horizontal' else QVBoxLayout()
        self.layout.addWidget(QLabel(label))
        self.layout.addWidget(self)
        self.addItems(items)
        if initial is not None:
            self.setCurrentText(initial)

class FontDialog(QDialog):
    min = 5
    max = 30
    figs = None
    def __init__(self):
        super().__init__()
        self.fontlist = sorted(font_manager.get_font_names())
        if len(rcParams["font.family"]) > 1:
            self.english_font = rcParams["font.family"][0]
            self.japanese_font = rcParams["font.family"][1]
        else:
            self.english_font = rcParams["font.family"][0]
            self.japanese_font = rcParams["font.family"][0]
        try:
            self.normalsize = str(int(rcParams["font.size"]))
        except:
            self.normalsize = "12"
        try:
            self.labelsize = str(int(rcParams["axes.labelsize"]))
        except:
            self.labelsize = "12"
        try:
            self.ticksize = str(int(rcParams["xtick.labelsize"]))
        except:
            self.ticksize = "12"
        try:
            self.legendsize = str(int(rcParams["legend.fontsize"]))
        except:
            self.legendsize = "12"
        self._create_main_frame()
        self._initialize()
        self.setWindowTitle("Font Setting")

    def _create_main_frame(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.inlayout = QHBoxLayout()
        self.japanese_font_combo = LabeledComboBox("Japanese Font", self.fontlist, self.japanese_font, layout='vertical')
        self.japanese_font_combo.currentTextChanged.connect(self.preview_font)
        self.english_font_combo = LabeledComboBox("English Font", self.fontlist, self.english_font, layout='vertical')
        self.english_font_combo.currentTextChanged.connect(self.preview_font)
        self.preview_figure = Figure(figsize=(2, 0.5))
        self.preview_canvas = FigureCanvas(self.preview_figure)
        self.gb1 = QGroupBox("Font Family")
        self.col1 = QVBoxLayout()
        self.col1.addLayout(self.japanese_font_combo.layout)
        self.col1.addLayout(self.english_font_combo.layout)
        self.col1.addWidget(self.preview_canvas)
        self.gb1.setLayout(self.col1)
        self.inlayout.addWidget(self.gb1)
        self.normaltext = LabeledComboBox("Default", [str(i) for i in range(self.min,self.max+1)], self.normalsize)
        self.labeltext = LabeledComboBox("Label", [str(i) for i in range(self.min,self.max+1)], self.labelsize)
        self.ticktext = LabeledComboBox("Tick", [str(i) for i in range(self.min,self.max+1)], self.ticksize)
        self.legendtext = LabeledComboBox("Legend", [str(i) for i in range(self.min,self.max+1)], self.legendsize)
        self.gb2 = QGroupBox("Font Size")
        self.col2 = QVBoxLayout()
        self.col2.addLayout(self.normaltext.layout)
        self.col2.addLayout(self.labeltext.layout)
        self.col2.addLayout(self.ticktext.layout)
        self.col2.addLayout(self.legendtext.layout)
        self.gb2.setLayout(self.col2)
        self.inlayout.addWidget(self.gb2)
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.main_layout.addLayout(self.inlayout)
        self.main_layout.addWidget(self.buttonbox)

    @property
    def font_family(self):
        return [self.english_font, self.japanese_font]
    
    def _initialize(self):
        self.preview_figure.clear()
        self.preview_figure.text(0.5, 0.5, "Langmuir型等温線", ha="center", va="center", fontsize=18, fontfamily=self.font_family)
        self.preview_canvas.draw()

    def preview_font(self):
        self.japanese_font = self.japanese_font_combo.currentText()
        self.english_font = self.english_font_combo.currentText()
        self.preview_figure.texts[0].set_fontfamily(self.font_family)
        self.preview_canvas.draw()

    def accept(self) -> None:
        self.normalsize = int(self.normaltext.currentText())
        self.labelsize = int(self.labeltext.currentText())
        self.ticksize = int(self.ticktext.currentText())
        self.legendsize = int(self.legendtext.currentText())
        self.gui_call("set_font", self.font_family)
        self.gui_call("set_fontsize", self.normalsize, labelsize=self.labelsize, ticksize=self.ticksize, legendsize=self.legendsize)
        return super().accept()
    
    def gui_call(self, function_name, *args, **kwargs):
        savefile.save_emulate_command(function_name, *args, **kwargs)
        f = getattr(self, function_name)
        f(*args, **kwargs)

    @classmethod
    def set_font(cls, font_family, fig=None):
        """change font family of all components
        Args:
            font_family (str or dict(str)): fontname or [fontname_english, fontname_japanese]
            fig (matplotlib.Figure, optional): target figure. If None, apply to all figures in figs. Defaults to None.
        """
        font = {'family': font_family}
        if fig is None:
            figs = cls.figs
        else:
            figs = [fig]
        for fig in figs:
            for t in fig.texts:
                t.set_fontfamily(font_family)
            for ax in fig.axes:
                ax.set_xlabel(ax.get_xlabel(),**font)
                ax.set_ylabel(ax.get_ylabel(),**font)
                form = ax.xaxis.get_major_formatter()
                loca = ax.xaxis.get_major_locator()
                lim = ax.get_xlim()
                ticks = np.linspace(lim[0],lim[1],100)
                ax.xaxis.set_ticks(ticks)
                ax.xaxis.set_ticklabels(ticks,**font)
                ax.xaxis.set_major_formatter(form)
                ax.xaxis.set_major_locator(loca)
                form = ax.yaxis.get_major_formatter()
                loca = ax.yaxis.get_major_locator()
                lim = ax.get_ylim()
                ticks = np.linspace(lim[0],lim[1],100)
                ax.yaxis.set_ticks(ticks)
                ax.yaxis.set_ticklabels(ticks,**font)
                ax.yaxis.set_major_formatter(form)
                ax.yaxis.set_major_locator(loca)
                if ax.legend_:
                    for text in ax.legend_.texts:
                        text.set_fontfamily(font_family)
                for t in ax.texts:
                    t.set_fontfamily(font_family)
                ax.title.set_fontfamily(font_family)
            fig.canvas.draw()
        rcParams["font.family"] = font_family

    @classmethod
    def set_fontsize(cls, defaultsize, labelsize=None, ticksize=None, legendsize=None, fig=None):
        """change font size of all components
        Args:
            defaultsize (float): default font size
            labelsize (float, optional): font size for x and y axis labels. If None, use defaultsize. Defaults to None.
            ticksize (float, optional): font size for x and y axis ticks. If None, use defaultsize. Defaults to None.
            legendsize (float, optional): font size for legend. If None, use defaultsize. Defaults to None.
            fig (matplotlib.Figure, optional): target figure. If None, apply to all figures in figs. Defaults to None.
        """
        if labelsize is None:
            labelsize = defaultsize
        if ticksize is None:
            ticksize = defaultsize
        if legendsize is None:
            legendsize = defaultsize
        if fig is None:
            figs = cls.figs
        else:
            figs = [fig]
        for fig in figs:
            for t in fig.texts:
                t.set_fontsize(defaultsize)
            for ax in fig.axes:
                ax.set_xlabel(ax.get_xlabel(),fontsize=labelsize)
                ax.set_ylabel(ax.get_ylabel(),fontsize=labelsize)
                ax.tick_params(labelsize=ticksize)
                if ax.legend_:
                    for text in ax.legend_.texts:
                        text.set_fontsize(legendsize)
                for t in ax.texts:
                    t.set_fontsize(defaultsize)
            fig.canvas.draw()
        rcParams["font.size"] = defaultsize
        rcParams["axes.labelsize"] = labelsize
        rcParams["xtick.labelsize"] = ticksize
        rcParams["ytick.labelsize"] = ticksize
        rcParams["legend.fontsize"] = legendsize

    @staticmethod
    def show():
        dialog = FontDialog()
        dialog.exec()

    @classmethod
    def set_figs(cls, figs):
        cls.figs = figs

if __name__ == "__main__":
    app = QApplication([])
    dialog = FontDialog()
    dialog._initialize()
    dialog.show()
    app.exec()
    print(dialog.font_family)