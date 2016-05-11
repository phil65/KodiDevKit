# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os
import platform
from .. import Utils
from urllib.request import Request, urlopen
import json
import base64
import logging

APP_NAME = "kodi"


class Kodi(object):

    def __init__(self, *args, **kwargs):
        self.settings = None
        self.po_files = []
        self.kodi_path = None

    @Utils.run_async
    def request_async(self, method, params):
        """
        send JSON command *data to Kodi in separate thread,
        also needs *settings for remote ip etc.
        """
        return self.request(method,
                            params)

    def request(self, method, params=None):
        """
        send JSON command *data to Kodi,
        also needs *settings for remote ip etc.
        """
        address = self.settings.get("kodi_address", "http://localhost:8080")
        if not address:
            return None
        data = {"jsonrpc": "2.0",
                "method": method,
                "id": 1}
        if params:
            data["params"] = params
        credentials = '{}:{}'.format(self.settings.get("kodi_username", "kodi"),
                                     self.settings.get("kodi_password", ""))
        headers = {'Content-Type': 'application/json',
                   'Authorization': b'Basic ' + base64.b64encode(credentials.encode('UTF-8'))}
        request = Request(url=address + "/jsonrpc",
                          data=json.dumps(data).encode('utf-8'),
                          headers=headers)
        try:
            result = urlopen(request).read()
            result = json.loads(result.decode("utf-8"))
            Utils.prettyprint(result)
            return result
        except Exception:
            return None

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

    def get_core_addon_folder(self):
        return os.path.join(self.kodi_path, "addons")

    def get_userdata_addons(self):
        addon_path = self.get_userdata_addon_folder()
        if not os.path.exists(addon_path):
            return []
        return [f for f in os.listdir(addon_path) if not os.path.isfile(f)]

    def load_settings(self, settings):
        self.settings = settings
        self.kodi_path = settings.get("kodi_path")
        self.update_labels()

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

    def get_addons(self):
        addon_path = os.path.join(self.get_userdata_folder(), "addons")
        if not os.path.exists(addon_path):
            return []
        return [f for f in os.listdir(addon_path) if not os.path.isfile(f)]
