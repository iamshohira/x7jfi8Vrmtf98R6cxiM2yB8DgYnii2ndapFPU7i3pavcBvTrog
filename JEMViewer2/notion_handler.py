import requests
import os
import pickle

class NotionHandler:
    def __init__(self, setting_dir):
        self.token_file = os.path.join(setting_dir, "notion_token")
        self.load_token()
        try:
            self.load_setting()
        except:
            # network error
            self.access_token = None

    def activate(self, tokens):
        token, db_id = tokens.split(";")
        access_token = "secret_" + token
        db_id = db_id
        with open(self.token_file,"wb") as f:
            pickle.dump([access_token, db_id], f)
        self.access_token = access_token
        self.db_id = db_id
        self.load_setting()
    
    @property
    def ok(self):
        return self.access_token != None

    def load_token(self):
        if os.path.exists(self.token_file):
            with open(self.token_file,"rb") as f:
                self.access_token, self.db_id = pickle.load(f)
        else:
            self.access_token = None
            self.db_id = None

    def load_setting(self):
        if not self.ok:
            return
        geturl = "https://api.notion.com/v1/databases/" + self.db_id + "/query" 
        headers = {
            "Authorization": self.access_token,
            "Content-Type": "application/json",
            "Notion-Version": "2021-08-16",
        }
        r = requests.post(geturl, headers=headers)
        getdata = r.json()
        res = getdata["results"]
        data = {}
        for item in res:
            obj = item["properties"]
            try:
                key = obj["key"]["title"][0]["text"]["content"]
                value = obj["value"]["rich_text"][0]["text"]["content"]
                data[key] = value
            except:
                pass
        self.data = data
