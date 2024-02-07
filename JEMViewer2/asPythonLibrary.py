from JEMViewer2.JEMViewer import FloatMainWindow, envs, savefile
from JEMViewer2.deco_figure import DecoFigure
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
import sys, os, shutil
import matplotlib.pyplot as plt
from typing import Union
import inspect

stack = inspect.stack()
for s in stack[1:]:
    m = inspect.getmodule(s[0])
    if m:
        call_from = m.__file__
        break

os.makedirs(envs.JEMDIR, exist_ok=True)
os.makedirs(envs.TEMP_DIR, exist_ok=True)
if not os.path.exists(envs.ADDON_DIR):
    shutil.copytree(envs.ADDON_TEMPRATE_DIR, envs.ADDON_DIR)
if not os.path.exists(envs.SETTING_DIR):
    shutil.copytree(envs.SETTING_TEMPRATE_DIR, envs.SETTING_DIR)
plt.style.use(envs.PLTPLOFILE)
app = QApplication(sys.argv)
app.setWindowIcon(QIcon(envs.LOGO))
main = FloatMainWindow(None, call_as_library=True, call_from = call_from)

def figure(num=1) -> Union[DecoFigure, list[DecoFigure]]:
    if num <= 1:
        return main.figs[0]
    else:
        for i in range(num-1):
            main.add_figure()
            savefile.save_addfigure()
        return main.figs

def show():
    main.show()
    app.exec()

def save(filename):
    main.filepath = filename
    main.save()

def loader_test(addon_py_file, loader_name, drop_file):
    with open(addon_py_file, 'r', encoding='utf-8') as f:
        command = f.read()
        main.ipython_w.executeCommand(command, hidden=True)
    execommand = f"{loader_name}('{drop_file}', ax)"
    main.ipython_w.executeCommand(execommand)
