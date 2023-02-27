from functools import wraps
import inspect
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.collections import PolyCollection
from matplotlib.text import Text
import re
from JEMViewer2.file_handler import savefile
    
class DecoFigure(Figure):
    def __init__(self, call_from, *args, **kwargs):
        self.childs_tree = {
            DecoFigure: ['axes'],
            Axes: ['lines','texts'],
        }
        self.call_from = call_from
        self.exclude = 'get_.*|stale_callback|draw|apply_aspect|ArtistList|set_id'
        super().__init__(*args, **kwargs)
        self._update_members(self)

    def _update_members(self, obj):
        # print("update_members", type(obj))
        if hasattr(obj, 'decolated'):
            return
        for name, fn in inspect.getmembers(obj):
            if name.startswith('__') or name.startswith('_') or re.match(self.exclude, name):
                continue
            if callable(getattr(obj, name)):
                setattr(obj, name, self._print_function(name, obj)(fn))
            setattr(obj, 'decolated', True)

    def _print_function(self, name, obj):
        def wrapper(fn):
            @wraps(fn)
            def decorate(*args, **kwargs):
                result = fn(*args, **kwargs)
                # print(name)
                if inspect.stack()[1].filename == self.call_from:
                    func_name = f"{self._header(obj)}.{name}"
                    savefile.save_emulate_command(func_name, *args, **kwargs)
                typ = type(obj)
                if typ in self.childs_tree:
                    for child in self.childs_tree[typ]:
                        # print("setting for", typ, child)
                        for item in getattr(obj, child):
                            self._update_members(item)
                return result
            return decorate
        return wrapper
    
    def _header(self, obj):
        typ = type(obj)
        header = ""
        if typ == DecoFigure:
            header = f'figs[{self.id}]'
        elif typ == Axes:
            axid = self.axes.index(obj)
            header = f'figs[{self.id}].axes[{axid}]'
        elif typ == Line2D:
            ax = obj.axes
            lineid = ax.lines.index(obj)
            axid = self.axes.index(ax)
            header = f'figs[{self.id}].axes[{axid}].lines[{lineid}]'
        # elif typ == PolyCollection:
        #     ax = obj.axes
        #     collectionid = ax.collections.index(obj)
        #     axid = self.axes.index(ax)
        #     header = f'figs[{self.id}].axes[{axid}].collections[{collectionid}]'
        elif typ == Text:
            ax = obj.axes
            textid = ax.texts.index(obj)
            axid = self.axes.index(ax)
            header = f'figs[{self.id}].axes[{axid}].texts[{textid}]'
        return header

    def set_id(self, id):
        self.id = id