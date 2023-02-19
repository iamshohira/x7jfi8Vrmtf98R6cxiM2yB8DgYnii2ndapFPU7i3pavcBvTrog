from urllib import request
from zipfile import ZipFile
import shutil, os

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

def current_version():
    with open(path_version_file, "r") as f:
        line = f.readline()
    return list(map(int, line.split(".")))

def latest_version():
    file = request.urlopen(version_file_url)
    lines = ""
    for line in file:
        lines += line.decode("utf-8")
    return list(map(int, lines.split(".")))

def download_zip():
    with request.urlopen(zip_url) as df:
        data = df.read()
        with open(path_zip, "wb") as f:
            f.write(data)

def extract_zip():
    with ZipFile(path_zip) as zp:
        zp.extractall(path_app)

def copy():
    shutil.rmtree(path_JEM)
    shutil.move(os.path.join(path_extracted,"JEMViewer2"), path_JEM)
    shutil.move(os.path.join(path_extracted,"VERSION"), path_app)

def clean():
    os.remove(path_zip)
    shutil.rmtree(path_extracted)

def update():
    cv = current_version()
    lv = latest_version()
    if lv[1] != cv[1]:
        print("Major update was released.\nPlease visit the official cite.")
        return
    if lv[2] == cv[2]:
        print(f"latest version: {'.'.join(cv)}")
        return
    download_zip()
    extract_zip()
    copy()
    clean()
    print("update complete")

if __name__ == "__main__":
    update()