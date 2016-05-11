# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os
from . import Utils
from . import addon
import logging


class Skin(addon.Addon):
    LANG_START_ID = 31000
    LANG_OFFSET = 0

    def __init__(self, *args, **kwargs):
        super(Skin, self).__init__(*args, **kwargs)
        self.type = "skin"
        for node in self.root.findall('.//res'):
            self.xml_folders.append(node.attrib["folder"])

    @property
    def lang_path(self):
        """
        returns the add-on language folder path
        """
        return os.path.join(self.path, "language")

    @property
    def primary_lang_folder(self):
        lang_folder = self.settings.get("language_folders")[0]
        lang_path = os.path.join(self.path, "language", lang_folder)
        if not os.path.exists(lang_path):
            os.makedirs(lang_path)
        return lang_path

    @property
    def media_path(self):
        """
        returns the add-on media folder path
        """
        return os.path.join(self.path, "media")

    def get_colors(self):
        """
        create color list by parsing all color files
        """
        self.colors = []
        color_path = os.path.join(self.path, "colors")
        if not self.addon.xml_file or not os.path.exists(color_path):
            return False
        for path in os.listdir(color_path):
            logging.info("found color file: " + path)
            file_path = os.path.join(color_path, path)
            root = Utils.get_root_from_file(file_path)
            for node in root.findall("color"):
                color_dict = {"name": node.attrib["name"],
                              "line": node.sourceline,
                              "content": node.text,
                              "file": file_path}
                self.colors.append(color_dict)
            logging.info("color list: %i colors found" % len(self.colors))