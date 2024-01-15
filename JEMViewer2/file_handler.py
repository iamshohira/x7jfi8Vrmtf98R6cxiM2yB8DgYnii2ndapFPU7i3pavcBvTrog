import random, pickle
import sys, os, string, shutil
import re, pathlib
import functools
from matplotlib.lines import Line2D
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np

exclude_command_list = [
    "edit()",
    "reboot()",
    "savefig",
    "reload_addon",
    "addon_store",
    ]

class Envs():
    RES_DIR = os.path.join(os.path.dirname(__file__),'resources')
    LOGO = os.path.join(os.path.join(RES_DIR,"JEMViewer2.png"))
    EXE_DIR = os.path.join(os.path.dirname(__file__))
    ADDON_TEMPRATE_DIR = os.path.join(os.path.dirname(__file__),'home','addon')
    SETTING_TEMPRATE_DIR = os.path.join(os.path.dirname(__file__),'home','setting')
    def __init__(self):
        pass

    def initialize(self, args):
        if args.local:
            self.JEMDIR = os.path.join(os.path.dirname(__file__),"..","HOME")
        else:
            self.JEMDIR = os.path.join(os.path.expanduser('~'),"JEMViewer2.3")
        self.ADDON_DIR = os.path.join(self.JEMDIR,'addon')
        self.SETTING_DIR = os.path.join(self.JEMDIR,'setting')
        self.TEMP_DIR = os.path.join(self.JEMDIR,'temp')
        self.PLTPLOFILE = os.path.join(self.SETTING_DIR,"default.mplstyle")
        if os.name == "nt":
            self.RUN = "start"
        else:
            self.RUN = "open"

envs = Envs()

class SaveFiles():
    def __init__(self):
        pass

    def mpl_to_dict(self, object):
        id = {}
        typ = type(object)
        if typ == Figure:
            id["figs"] = self.figs.index(object)
        elif typ == Axes:
            id["figs"] = self.figs.index(object.figure)
            id["axes"] = self.figs[id["figs"]].axes.index(object)
        elif typ == Line2D:
            id["figs"] = self.figs.index(object.axes.figure)
            id["axes"] = self.figs[id["figs"]].axes.index(object.axes)
            id["lines"] = self.figs[id["figs"]].axes[id["axes"]].lines.index(object)
        return id

    def dict_to_mpl(self, dict):
        object = self.figs[dict["figs"]]
        if "axes" in dict.keys():
            object = object.axes[dict["axes"]]
        if "lines" in dict.keys():
            object = object.lines[dict["lines"]]
        return object
    
    def emulate_args(self, x):
        typ = type(x)
        if typ == str:
            return f'"{x}"'
        elif typ in [Figure, Axes, Line2D]:
            id_dict = self.mpl_to_dict(x)
            return str(id_dict)
        elif typ == np.ndarray:
            name = self.randomname(8)
            self.save_npdata(name, x)
            return name
        else:
            return str(x)
    
    def save_emulate_command(self, function_name, *args, **kwargs):
        str_args = []
        for arg in args:
            str_args.append(self.emulate_args(arg))
        for k, v in kwargs.items():
            str_args.append(f"{k} = {self.emulate_args(v)}")
        command = f"{function_name}({','.join(str_args)})"
        self.save_commandline(command)

    def save_gui(self,f):
        @functools.wraps(f)
        def wrapper(self_, *args, **kwargs): # eliminate self
            self.save_emulate_command(f.__name__, *args, **kwargs)
            return f(self_, *args, **kwargs)
        return wrapper

    def save_commandline(self, command):
        with open(self.logfilename, "a", encoding='utf-8') as f:
            print(command, file=f)

    def set_workspace(self,home_dir):
        self.make_tmpdir(home_dir)
        self.make_commandfile()

    def set_figure(self,figs):
        self.figs = figs

    def make_tmpdir(self,home_dir):
        self.dirname = os.path.join(home_dir,self.randomname(10))
        os.makedirs(self.dirname)
        if os.name == "nt": #windows convert \\ to /
            pldir = pathlib.Path(self.dirname)
            self.dirname = pldir.as_posix()

    def make_commandfile(self):
        self.logfilename = os.path.join(self.dirname,'command.py')
        with open(self.logfilename, 'w', encoding='utf-8') as f:
            pass
        
    def save_command(self,command,fileparse=False,alias=True,exclude = exclude_command_list):
        for e in exclude:
            if e in command:
                return
        if fileparse:
            command = command.replace("'",'"')
            match = re.findall(r'"(.*?)"',command)
            for filename in match:
                if filename == '.':
                    continue
                if os.path.isfile(filename):
                    filename = os.path.abspath(filename)
                    savedname = os.path.join(self.dirname, self.splittedfile(filename))
                    os.makedirs(os.path.dirname(savedname),exist_ok=True)
                    shutil.copy(filename, savedname)
                    command = command.replace('"{}"'.format(filename,),"os.path.join(savedir,\"{}\")".format(self.splittedfile(filename),))
                if os.path.isdir(filename):
                    filename = os.path.abspath(filename)
                    savedname = os.path.join(self.dirname, self.splittedfile(filename))
                    os.makedirs(os.path.dirname(savedname),exist_ok=True)
                    shutil.copytree(filename, savedname)
                    command = command.replace('"{}"'.format(filename,),"os.path.join(savedir,\"{}\")".format(self.splittedfile(filename),))
        self.save_commandline(command)
        if alias:
            self.save_commandline("update_alias()")

    def save_npdata(self,new_name,data):
        pickle.dump(data,open(os.path.join(self.dirname,new_name),'wb'))
        self.save_commandline(f"{new_name} = pickle.load(open(os.path.join(savedir,\"{new_name}\"),\"rb\"))")
        self.save_commandline(f"justnow = {new_name}")
        self.save_commandline("update_alias()")

    def save_plot(self, new_name, figaxid, data, label):
        pickle.dump(data,open(os.path.join(self.dirname,new_name),'wb'))
        self.save_commandline(f"_ = pickle.load(open(os.path.join(savedir,\"{new_name}\"),\"rb\"))")
        self.save_commandline("lines = []")            
        self.save_commandline("for i in range(1,len(_)):")
        self.save_commandline(f"    line, = figs[{figaxid['figs']}].axes[{figaxid['axes']}].plot(_[0],_[i],label=\"{label}\")")
        self.save_commandline("    lines.append(line)")
        self.save_commandline(f"{new_name} = lines if len(lines) > 1 else lines[0]")
        self.save_commandline(f"justnow = {new_name}")
        self.save_commandline("update_alias()")

    def save_customloader(self,lis):
        functionname = lis[0]
        filename = lis[1]
        newname = lis[3]
        figaxid = lis[4]
        filename = os.path.abspath(filename)
        savedname = os.path.join(self.dirname, self.splittedfile(filename))
        os.makedirs(os.path.dirname(savedname),exist_ok=True)
        if os.path.isfile(filename):
            shutil.copy(filename,savedname)
        if os.path.isdir(filename):
            shutil.copytree(filename,savedname)
        self.save_commandline(f"{newname} = {functionname}(os.path.join(savedir,\"{self.splittedfile(filename)}\"),figs[{figaxid['figs']}].axes[{figaxid['axes']}])")
        self.save_commandline(f"justnow = {newname}")
        self.save_commandline("update_alias()")

    def splittedfile(self, filename):
        fp = os.path.splitdrive(filename)[1]
        if os.name == "nt": #windows convert \\ to /s
            plfp = pathlib.Path(fp)
            fp = plfp.as_posix()
        return fp[1:]

    def randomname(self,n):
        randlst = [random.choice(string.ascii_lowercase) for i in range(n)]
        return 'jem_' + ''.join(randlst)

    def remove_tmpdir(self):
        shutil.rmtree(self.dirname)

    def save(self,filepath):
        shutil.make_archive(filepath, format='zip', root_dir=self.dirname)
        shutil.move(filepath + ".zip", filepath)

    def open(self,filepath):
        shutil.unpack_archive(filepath,format='zip',extract_dir=self.dirname)

    def load(self):
        with open(self.logfilename, 'r', encoding='utf-8') as f:
            command = f.read()
        return command

    def load_command_py(self):
        with open(self.logfilename,"r", encoding='utf-8') as f:
            command = f.read()
        return command

    def save_log(self,log):
        pickle.dump(log,open(os.path.join(self.dirname,"log"),'wb'))

    def load_log(self):
        with open(os.path.join(self.dirname,"log"),'rb') as f:
            log = pickle.load(f)
        return log

    def save_removefigure(self, id_):
        self.save_commandline(f"remove_figure({id_})")

    def save_addfigure(self):
        self.save_commandline("add_figure()")

    def save_subplotsparam(self, is_tight, fig_id, parameters):
        self.save_commandline(f"figs[{fig_id}].set_tight_layout({is_tight})")
        if is_tight:
            self.save_commandline(f"figs[{fig_id}].tight_layout()")
        else:
            self.save_commandline(f"figs[{fig_id}].subplots_adjust({parameters})")

savefile = SaveFiles()