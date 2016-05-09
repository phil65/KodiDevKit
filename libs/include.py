# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details


class Include(dict):

    def __init__(self, *args, **kwargs):
        super(Include, self).__init__(*args, **kwargs)
        self.node = kwargs.get("node")
        self.filename = kwargs.get("filename")
        self.file = kwargs.get("file")

    def __getitem__(self, key):
        if key == "line":
            return self.line
        if key == "type":
            return self.tag
        if key == "name":
            return self.name
        if key == "filename":
            return self.filename
        if key == "file":
            return self.file
        super(Include, self).__getitem__(key)

    @property
    def line(self):
        return self.node.sourceline

    @property
    def tag(self):
        return self.node.tag

    @property
    def name(self):
        return self.node.text

    @property
    def filename(self):
        return self.filename

    @property
    def file(self):
        return self.file
