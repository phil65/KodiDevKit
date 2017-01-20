# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

from lxml import etree as ET
import os


class Include(dict):

    constant_attribs = {"x", "y", "width", "height", "center", "max", "min", "w", "h", "time", "acceleration", "delay", "start", "end", "center", "border", "repeat"}
    constant_nodes = {"posx", "posy", "left", "centerleft", "right", "centerright", "top", "centertop", "bottom", "centerbottom", "width", "height", "offsetx", "offsety", "textoffsetx", "textoffsety", "textwidth", "spinposx", "spinposy", "spinwidth", "spinheight", "radioposx", "radioposy", "radiowidth", "radioheight", "sliderwidth", "sliderheight", "itemgap", "bordersize", "timeperimage", "fadetime", "pauseatend", "depth"}
    exp_nodes = {"visible", "enable", "usealttexture", "selected"}
    exp_attribs = {"condition"}

    def __init__(self, node, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node = node
        self.file = kwargs.get("file")
        if self.node.getnext() is not None:
            self.length = self.node.getnext().sourceline - self.node.sourceline
        else:
            self.length = None

    def __getitem__(self, key):
        if key == "line":
            return self.line
        elif key == "type":
            return self.tag
        elif key == "name":
            return self.name
        elif key == "filename":
            return self.filename
        elif key == "file":
            return self.file
        elif key == "content":
            return ET.tostring(self.node, pretty_print=True, encoding="unicode")
        elif key == "length":
            return self.length
        return super().__getitem__(key)

    def get(self, key):
        return self.__getitem__(key)

    @property
    def line(self):
        return self.node.sourceline

    @property
    def tag(self):
        return self.node.tag

    @property
    def content(self):
        return self.node.text

    @property
    def name(self):
        return self.node.attrib.get("name")

    @property
    def filename(self):
        return os.path.basename(self.file)

