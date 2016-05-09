# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os
from . import Utils


class Addon(object):
    LANG_START_ID = 32000
    LANG_OFFSET = 2

    def __init__(self, *args, **kwargs):
        self.type = "python"
        self.project_path = kwargs.get("project_path")
        self.xml_file = os.path.join(self.project_path, "addon.xml")
        self.root_path = kwargs.get("project_path")
        root = Utils.get_root_from_file(self.xml_file)
        for item in root.xpath("/addon[@id]"):
            self.name = item.attrib["id"]
            break
        self.xml_folders = []
        paths = [os.path.join(self.root_path, "resources", "skins", "Default", "720p"),
                 os.path.join(self.root_path, "resources", "skins", "Default", "1080i")]
        folder = Utils.check_paths(paths)
        self.xml_folders.append(folder)

    @property
    def lang_path(self):
        """
        returns the add-on language folder path
        """
        return os.path.join(self.root_path, "resources", "language")

    @property
    def primary_lang_folder(self):
        lang_folder = self.settings.get("language_folders")[0]
        lang_path = os.path.join(self.root_path, "resources", "language", lang_folder)
        if not os.path.exists(lang_path):
            os.makedirs(lang_path)
        return lang_path

    @property
    def media_path(self):
        """
        returns the add-on media folder path
        """
        return os.path.join(self.root_path, "resources", "skins", "Default", "media")

    @staticmethod
    def by_project(project_path):
        xml_file = os.path.join(project_path, "addon.xml")
        root = Utils.get_root_from_file(xml_file)
        if root.find(".//import[@addon='xbmc.python']") is None:
            from . import skin
            return skin.Skin(project_path=project_path)
        else:
            return Addon(project_path=project_path)
            # TODO: parse all python skin folders correctly
