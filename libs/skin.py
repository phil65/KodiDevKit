# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os
from . import Utils
from . import addon
import logging
from lxml import etree as ET


class Skin(addon.Addon):

    """
    Class representing a Kodi skin.
    """

    LANG_START_ID = 31000
    LANG_OFFSET = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kodi_version = self.root.find(".//import[@addon='xbmc.gui']")
        self.type = "skin"
        self.update_include_list()
        self.get_colors()
        self.get_fonts()

    def load_xml_folders(self):
        """
        get all xml folders from addon.xml
        """
        self.xml_folders = {node.attrib["folder"] for node in self.root.findall('.//res')}

    @property
    def lang_path(self):
        """
        returns the skin language folder path
        """
        return os.path.join(self.path, "language")

    @property
    def theme_path(self):
        """
        returns the skin theme folder path
        """
        return os.path.join(self.path, "themes")

    @property
    def primary_lang_folder(self):
        """
        returns the primary lang folder, as chosen in settings
        """
        lang_folder = self.settings.get("language_folders")[0]
        lang_path = os.path.join(self.path, "language", lang_folder)
        if not os.path.exists(lang_path):
            os.makedirs(lang_path)
        return lang_path

    @property
    def media_path(self):
        """
        returns the skin media folder path
        """
        return os.path.join(self.path, "media")

    def get_colors(self):
        """
        create color list by parsing all color files
        """
        self.colors = []
        color_path = os.path.join(self.path, "colors") if self.path else ""
        if not self.xml_file or not os.path.exists(color_path):
            return False
        for path in os.listdir(color_path):
            file_path = os.path.join(color_path, path)
            root = Utils.get_root_from_file(file_path)
            if root is None:
                logging.info("Invalid color file: {}".format(file_path))
                continue
            for node in root.findall("color"):
                color = {"name": node.attrib["name"],
                         "line": node.sourceline,
                         "content": node.text,
                         "file": file_path}
                self.colors.append(color)
            logging.info("found color file %s including %i colors" % (path, len(self.colors)))
        self.color_labels = {i["name"] for i in self.colors}

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
            self.font_file = Utils.check_paths(paths)
            if not self.font_file:
                return False
            self.fonts[folder] = []
            root = Utils.get_root_from_file(self.font_file)
            for node in root.find("fontset").findall("font"):
                font = {"name": node.find("name").text,
                        "size": node.find("size").text,
                        "line": node.sourceline,
                        "content": ET.tostring(node, pretty_print=True, encoding="unicode"),
                        "file": self.font_file,
                        "filename": node.find("filename").text}
                self.fonts[folder].append(font)

    def get_media_files(self):
        """
        yields relative paths of all files in "media" directory
        """
        for path, _, files in os.walk(self.media_path):
            if "studio" in path or "recordlabel" in path:
                continue
            for filename in files:
                img_path = os.path.join(path, filename)
                img_path = img_path.replace(self.media_path, "").replace("\\", "/")
                if img_path.startswith("/"):
                    img_path = img_path[1:]
                yield img_path

    def update_include_list(self):
        """
        create include list by parsing all include files starting with includes.xml
        """
        self.includes = {}
        for folder in self.xml_folders:
            xml_folder = os.path.join(self.path, folder)
            paths = [os.path.join(xml_folder, "Includes.xml"),
                     os.path.join(xml_folder, "includes.xml")]
            self.include_files[folder] = []
            self.includes[folder] = []
            include_file = Utils.check_paths(paths)
            self.update_includes(include_file)
            logging.info("Include List: %i nodes found in '%s' folder." % (len(self.includes[folder]), folder))

    def update_includes(self, xml_file):
        """
        recursive, walks through include files and updates include list and include file list
        """
        if not os.path.exists(xml_file):
            logging.info("Could not find include file " + xml_file)
            return None
        folder = xml_file.split(os.sep)[-2]
        logging.info("found include file: " + xml_file)
        self.include_files[folder].append(xml_file)
        tags = ["include", "variable", "constant", "expression"]
        self.includes[folder] += Utils.get_tags_from_file(path=xml_file,
                                                          node_tags=tags)
        root = Utils.get_root_from_file(xml_file)
        if root is None:
            return None
        for node in root.findall("include"):
            if "file" in node.attrib and node.attrib["file"] != "script-skinshortcuts-includes.xml":
                xml_file = os.path.join(self.path, folder, node.attrib["file"])
                self.update_includes(xml_file)

    def reload(self, path):
        """
        update include, color and font infos, depending on open file
        """
        folder = path.split(os.sep)[-2]
        if folder in self.include_files:
            if path in self.include_files[folder]:
                self.update_include_list()
        if path.endswith("colors/defaults.xml"):
            self.get_colors()
        if path.endswith(("Font.xml", "font.xml")):
            self.get_fonts()

    def get_font_refs(self):
        """
        get font references from all window files
        """
        font_refs = {}
        for folder in self.xml_folders:
            font_refs[folder] = []
            for xml_file in self.window_files[folder]:
                path = os.path.join(self.path, folder, xml_file)
                matches = []
                root = Utils.get_root_from_file(path)
                if root is None:
                    return None
                for node in root.xpath(".//font"):
                    if node.getchildren():
                        continue
                    item = Font(node=node,
                                file=path)
                    matches.append(item)
                font_refs[folder].extend(matches)
        return font_refs

    def get_themes(self):
        """
        returns a list of all theme names, taken from "themes" folder
        """
        return [folder for folder in os.listdir(os.path.join(self.path, "themes"))]

    def resolve_include(self, ref, folder):
        if not ref.text:
            return None
        include_names = [item["name"] for item in self.addon.includes[folder]]
        if ref.text not in include_names:
            return None
        index = include_names.index(ref.text)
        node = self.addon.includes[folder][index]
        root = ET.fromstring(node["content"])
        return self.resolve_includes(root, folder)

    def resolve_includes(self, xml_source, folder):
        for node in xml_source.xpath(".//include"):
            if node.text:
                new_include = self.resolve_include(node, folder)
                if new_include is not None:
                    node.getparent().replace(node, new_include)
        return xml_source

    def get_constants(self, folder):
        return [i["name"] for i in self.includes[folder] if i["type"] == "constant"]
