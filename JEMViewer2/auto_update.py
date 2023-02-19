from urllib import request
from zipfile import ZipFile
import shutil, os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

class AutoUpdater:
    # git url
    version_file_url = "https://raw.githubusercontent.com/iamshohira/x7jfi8Vrmtf98R6cxiM2yB8DgYnii2ndapFPU7i3pavcBvTrog/master/VERSION"
    zip_url = "https://github.com/iamshohira/x7jfi8Vrmtf98R6cxiM2yB8DgYnii2ndapFPU7i3pavcBvTrog/archive/refs/heads/master.zip"
    extractname = "x7jfi8Vrmtf98R6cxiM2yB8DgYnii2ndapFPU7i3pavcBvTrog-master"
    zipname = "dl.zip"

    # path setting
    # app - JEMViewer2 - auto_update.py
    #     L VERSION
    path_JEM = os.path.dirname(__file__)
    path_app = os.path.dirname(path_JEM)
    path_zip = os.path.join(path_app, zipname)
    path_extracted = os.path.join(path_app, extractname)
    path_version_file = os.path.join(path_app, "VERSION")
    path_git = os.path.join(path_app, ".git")

    def __init__(self):
        self.update()

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

    def download_zip(self):
        with request.urlopen(self.zip_url) as df:
            data = df.read()
            with open(self.path_zip, "wb") as f:
                f.write(data)

    def extract_zip(self):
        with ZipFile(self.path_zip) as zp:
            zp.extractall(self.path_app)

    def copy(self):
        shutil.rmtree(self.path_JEM)
        shutil.move(os.path.join(self.path_extracted,"JEMViewer2"), self.path_JEM)
        shutil.move(os.path.join(self.path_extracted,"VERSION"), self.path_version_file)

    def clean(self):
        os.remove(self.path_zip)
        shutil.rmtree(self.path_extracted)

    def update(self):
        if os.path.exists(self.path_git):
            print("master files")
            return
        cv = self.current_version()
        lv = self.latest_version()
        if lv[1] != cv[1]:
            print("Major update was released.\nPlease visit the official cite.")
            return
        if lv[2] == cv[2]:
            print(f"latest version")
            return
        self.download_zip()
        self.extract_zip()
        self.copy()
        self.clean()
        self.finish()

    def finish(self):
        reply = QMessageBox.question(self,'Update information',
            f"Version {self.lv} has been downloaded. To apply the changes, please restart the software. Would you like to view the update logs?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            print("open sites")

if __name__ == "__main__":
    updater = AutoUpdater()
    updater.update()