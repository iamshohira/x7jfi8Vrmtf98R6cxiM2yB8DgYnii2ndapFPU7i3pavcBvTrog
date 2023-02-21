import requests
from prettytable import PrettyTable
import os, webbrowser
import pickle
import subprocess

class AddonInstaller:
    def __init__(self, addon_dir, notion_handler):
        self.addon_dir = addon_dir
        self.notion_handler = notion_handler
        self.addons = None
        self.token_file = os.path.join(self.addon_dir,"notion_token")

    def load_addon(self):
        if not self.notion_handler.ok:
            print("You need to activate notion_handler first.\nPlease check the manual site.")
            return False
        geturl = "https://api.notion.com/v1/databases/" + self.notion_handler.data["addon_database_id"] + "/query" 
        headers = {
            "Authorization": self.notion_handler.access_token,
            "Content-Type": "application/json",
            "Notion-Version": "2021-08-16",
        }
        r = requests.post(geturl, headers=headers)
        getdata = r.json()
        res = getdata["results"]
        addons = {}
        for data in res:
            obj = data["properties"]
            try:
                if obj["Status"]["select"]["name"] == "archive":
                    continue
            except:
                pass
            try:
                name = obj["名前"]["title"][0]["plain_text"]
            except:
                continue
            try:
                filename = obj["script file"]["files"][0]["name"]
                fileurl = obj["script file"]["files"][0]["file"]["url"]
            except:
                continue
            try:
                description = obj["一言説明"]["rich_text"][0]["plain_text"]
            except:
                description = ""
            addons[name] = {
                "description": description,
                "filename": filename,
                "fileurl": fileurl,
            }
        self.addons = addons
        return True

    def list(self):
        if self.addons == None:
            if not self.load_addon():
                return
        table = PrettyTable()
        table.align = "l"
        table.field_names = ["Addon", "Description"]
        for k,v in self.addons.items():
            table.add_row([k, v["description"]])
        print(table)

    def install(self, addon_name):
        if self.addons == None:
            if not self.load_addon():
                return
        addon = self.addons[addon_name]
        urldata = requests.get(addon["fileurl"]).content
        with open(os.path.join(self.addon_dir, addon["filename"]), "wb") as f:
            f.write(urldata)

    def install_all(self):
        if self.addons == None:
            if not self.load_addon():
                return
        for k in self.addons.keys():
            self.install(k)

    def open_dir(self):
        if os.name == "nt":
            run = "start"
        else:
            run = "open"
        subprocess.run([run, self.addon_dir])

    def open_vscode(self):
        try:
            subprocess.run(["code", self.addon_dir])
        except:
            pass

