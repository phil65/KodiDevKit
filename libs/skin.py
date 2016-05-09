# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os
from . import Utils
from . import addon


class Skin(addon.Addon):
    LANG_START_ID = 31000
    LANG_OFFSET = 0

    def __init__(self, *args, **kwargs):
        self.type = "skin"
        self.xml_folders = []
        self.project_path = kwargs.get("project_path")
        self.xml_file = os.path.join(self.project_path, "addon.xml")
        root = Utils.get_root_from_file(self.xml_file)
        for node in root.findall('.//res'):
            self.xml_folders.append(node.attrib["folder"])

    @property
    def lang_path(self):
        """
        returns the add-on language folder path
        """
        return os.path.join(self.project_path, "language")

    @property
    def primary_lang_folder(self):
        lang_folder = self.settings.get("language_folders")[0]
        lang_path = os.path.join(self.project_path, "language", lang_folder)
        if not os.path.exists(lang_path):
            os.makedirs(lang_path)
        return lang_path

    @property
    def media_path(self):
        """
        returns the add-on media folder path
        """
        return os.path.join(self.project_path, "media")
