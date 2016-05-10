# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os
import platform
from . import Utils

APP_NAME = "kodi"


class Kodi(object):

    def __init__(self, *args, **kwargs):
        self.settings = None
        self.po_files = []

    def get_userdata_folder(self):
        """
        return userdata folder based on platform and portable setting
        """
        if platform.system() == "Linux":
            return os.path.join(os.path.expanduser("~"), ".%s" % APP_NAME)
        elif platform.system() == "Windows":
            if self.settings.get("portable_mode"):
                return os.path.join(self.settings.get("kodi_path"), "portable_data")
            else:
                return os.path.join(os.getenv('APPDATA'), APP_NAME)
        elif platform.system() == "Darwin":
            return os.path.join(os.path.expanduser("~"), "Application Support", APP_NAME, "userdata")

    def get_userdata_addon_folder(self):
        return os.path.join(self.get_userdata_folder(), "addons")

    def get_userdata_addons(self):
        addon_path = self.get_userdata_addon_folder()
        if not os.path.exists(addon_path):
            return []
        return [f for f in os.listdir(addon_path) if not os.path.isfile(f)]

    def load_settings(self, settings):
        self.settings = settings

    def update_labels(self):
        """
        get core po files
        """
        self.po_files = self.get_po_files(os.path.join(self.get_userdata_folder(), "addons"))
        if not self.po_files:
            self.po_files = self.get_po_files(os.path.join(self.kodi_path, "addons"))

    def get_po_files(self, folder):
        """
        get list with pofile objects
        """
        po_files = []
        for item in self.settings.get("language_folders"):
            path = Utils.check_paths([os.path.join(folder, item, "strings.po"),
                                      os.path.join(folder, item, "resources", "strings.po")])
            if os.path.exists(path):
                po_files.append(Utils.get_po_file(path))
        return po_files
