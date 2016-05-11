# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os
from . import Utils
from . import addon
import logging
from lxml import etree as ET
import string


class Skin(addon.Addon):
    LANG_START_ID = 31000
    LANG_OFFSET = 0

    def __init__(self, *args, **kwargs):
        super(Skin, self).__init__(*args, **kwargs)
        self.type = "skin"
        self.get_colors()
        self.get_fonts()

    def load_xml_folders(self):
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
        if not self.xml_file or not os.path.exists(color_path):
            return False
        for path in os.listdir(color_path):
            file_path = os.path.join(color_path, path)
            root = Utils.get_root_from_file(file_path)
            for node in root.findall("color"):
                color = {"name": node.attrib["name"],
                         "line": node.sourceline,
                         "content": node.text,
                         "file": file_path}
                self.colors.append(color)
            logging.info("found color file %s including %i colors" % (path, len(self.colors)))

    def get_fonts(self):
        """
        create font dict by parsing first fontset
        """
        if not self.xml_file or not self.xml_folders:
            return False
        self.fonts = {}
        for folder in self.xml_folders:
            paths = [os.path.join(self.path, folder, "Font.xml"),
                     os.path.join(self.path, folder, "font.xml")]
            font_file = Utils.check_paths(paths)
            if not font_file:
                return False
            self.fonts[folder] = []
            root = Utils.get_root_from_file(font_file)
            for node in root.find("fontset").findall("font"):
                string_dict = {"name": node.find("name").text,
                               "size": node.find("size").text,
                               "line": node.sourceline,
                               "content": ET.tostring(node, pretty_print=True, encoding="unicode"),
                               "file": font_file,
                               "filename": node.find("filename").text}
                self.fonts[folder].append(string_dict)

    def get_color_info(self, color_string):
        color_info = ""
        for item in self.colors:
            if item["name"] == color_string:
                color_hex = "#" + item["content"][2:]
                cont_color = Utils.get_cont_col(color_hex)
                alpha_percent = round(int(item["content"][:2], 16) / (16 * 16) * 100)
                color_info += '%s&nbsp;<a href="test" style="background-color:%s;color:%s">%s</a> %d %% alpha<br>' % (os.path.basename(item["file"]), color_hex, cont_color, item["content"], alpha_percent)
        if color_info:
            return color_info
        if all(c in string.hexdigits for c in color_string) and len(color_string) == 8:
            color_hex = "#" + color_string[2:]
            cont_color = Utils.get_cont_col(color_hex)
            alpha_percent = round(int(color_string[:2], 16) / (16 * 16) * 100)
            return '<a href="test" style="background-color:%s;color:%s">%d %% alpha</a>' % (color_hex, cont_color, alpha_percent)

