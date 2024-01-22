from urllib import request
from zipfile import ZipFile
import shutil, os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import webbrowser

class AutoUpdater:
    # git url
    version_file_url = "https://raw.githubusercontent.com/iamshohira/x7jfi8Vrmtf98R6cxiM2yB8DgYnii2ndapFPU7i3pavcBvTrog/master/JEMViewer2/VERSION"
    zip_url = "https://github.com/iamshohira/x7jfi8Vrmtf98R6cxiM2yB8DgYnii2ndapFPU7i3pavcBvTrog/archive/refs/heads/{branch}.zip"
    extractname = "x7jfi8Vrmtf98R6cxiM2yB8DgYnii2ndapFPU7i3pavcBvTrog-{branch}"
    zipname = "dl.zip"

    # path setting
    # app - JEMViewer2 - auto_update.py
    #     L VERSION
    path_JEM = os.path.dirname(__file__)
    path_app = os.path.dirname(path_JEM)
    path_zip = os.path.join(path_app, zipname)
    path_extracted = os.path.join(path_app, extractname)
    path_version_file = os.path.join(path_JEM, "VERSION")
    path_git = os.path.join(path_app, ".git")

    def __init__(self, notion_handler):
        self.notion_handler = notion_handler
        self.header = "\nJEMViewer 2\n"
        self.can_update = False
        self.debug = False
        try:
            self.check_update()
        except:
            self.header += "Network error\n"
            self.header += "Please check your network connection.\n\n"

    def current_version(self):
        with open(self.path_version_file, "r") as f:
            line = f.readline()
        self.cv = line
        return list(map(int, line.split(".")))

    def latest_version(self):
        request.urlcleanup()
        file = request.urlopen(self.version_file_url)
        lines = ""
        for line in file:
            lines += line.decode("utf-8")
        self.lv = lines
        return list(map(int, lines.split(".")))

    def download_zip(self, branch):
        with request.urlopen(self.zip_url.format(branch=branch)) as df:
            data = df.read()
            with open(self.path_zip, "wb") as f:
                f.write(data)

    def extract_zip(self):
        with ZipFile(self.path_zip) as zp:
            zp.extractall(self.path_app)

    def copy(self, branch):
        shutil.rmtree(self.path_JEM)
        shutil.move(os.path.join(self.path_extracted.format(branch=branch),"JEMViewer2"), self.path_JEM)

    def clean(self, branch):
        os.remove(self.path_zip)
        shutil.rmtree(self.path_extracted.format(branch=branch))

    def check_update(self):
        if os.path.exists(self.path_git):
            self.header += "\nThis is the master files.\nEnter debug mode.\n"
            self.debug = True
        cv = self.current_version()
        lv = self.latest_version()
        if lv[1] != cv[1]:
            self.header += "\nA major update has been released.\nPlease visit the official website.\n\n"
            return
        if lv[2] == cv[2]:
            self.header += f"\nVersion {self.cv} (latest)\n\n"
            return
        self.can_update = True

    def update(self, branch):
        if branch == None:
            branch = "master"
        if not self.debug:
            self.download_zip(branch)
            self.extract_zip()
            self.copy(branch)
            self.clean(branch)
        return self.finish()

    # def finish(self):
    #     if self.notion_handler.ok:
    #         reply = QMessageBox.question(None,'Update information',
    #             f"Version {self.lv} has been downloaded. The software will now shut down to apply the changes. Would you like to view the update logs?",
    #             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    #         if reply == QMessageBox.Yes:
    #             webbrowser.open_new(self.notion_handler.data["updatelog_for2.3_url"])
    #     else:
    #         QMessageBox.information(None,'Update information',
    #             f"Version {self.lv} has been downloaded. The software will now shut down to apply the changes.")
        
    def finish(self):
        if self.notion_handler.ok:
            webbrowser.open_new(self.notion_handler.data["updatelog_for2.3_url"])
        msg = QMessageBox(None)
        msg.setWindowTitle("Update information")
        msg.setText(f"Version {self.lv} has been downloaded. The software requires to restart to apply the changes.")
        return msg

if __name__ == "__main__":
    updater = AutoUpdater(None)
    print(updater.zip_url.format(branch="beta"))