# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
KodiDevKit is a tool to assist with Kodi skinning / scripting using Sublime Text 3
"""


import os
import re
from lxml import etree as ET
import logging
import string
import json
import copy
from . import utils
from .addon import Addon
from .kodi import kodi
from . import imageparser

ns = ET.FunctionNamespace(None)
ns['lower-case'] = lambda context, s: str.lower(s)

# allowed child nodes for different control types (+ some other nodes)
TAG_CHECKS = [[".//content/*", {"item", "include"}],
              [".//itemlayout/* | .//focusedlayout/*", {"control", "include"}],
              ["/includes/*", {"include", "default", "constant", "variable", "expression"}],
              ["/window/*", {"include", "defaultcontrol", "depth", "menucontrol", "onload", "onunload",
                             "controls", "allowoverlay", "views", "coordinates", "animation", "visible",
                             "zorder", "fontset", "backgroundcolor"}],
              ["/fonts/*", {"fontset"}],
              [".//variable/*", {"value"}]]
# allowed attributes for some specific nodes
# all_tags = [d[0] for d in att_checks]
# check correct parantheses for some nodes
BRACKET_TAGS = {"visible", "enable", "usealttexture", "selected", "expression"}
# check some nodes to use noop instead of "-" / empty
NOOP_TAGS = {"onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback"}

POS_TAGS = {"posx", "posy", "left", "right", "top", "bottom", "centerleft", "centerright", "centertop", "centerbottom"}
# check that some nodes only exist once on each level
# TODO: special cases: label for fadelabel
DOUBLE_TAGS = {"camera", "posx", "posy", "top", "bottom", "left", "right", "centertop", "centerbottom",
               "centerleft", "centerright", "width", "height", "colordiffuse", "texturefocus",
               "texturenofocus", "font", "selected", "textcolor", "disabledcolor", "selectedcolor",
               "usecontrolcoords", "shadowcolor", "align", "aligny", "textoffsetx", "textoffsety",
               "pulseonselect", "textwidth", "focusedcolor", "invalidcolor", "angle", "hitrect",
               "orientation", "offsetx", "offsety"}
# check that some nodes only contain specific text
# check that some attributes may only contain specific values
ALLOWED_VALUES = {"align": {"left", "center", "right", "justify"},
                  "aligny": {"top", "center", "bottom"},
                  "bool": {"true", "false"},
                  "orientation": {"horizontal", "vertical"},
                  "aspect": {"scale", "stretch", "center", "keep"},
                  "subtype": {"page", "int", "float", "text"},
                  "action": {"volume", "seek"},
                  "viewtype": {"list", "icon", "biglist", "bigicon", "wide", "bigwide", "wrap", "bigwrap", "info", "biginfo"},
                  "tween": {"quadratic", "linear", "sine", "cubic", "back", "bounce", "circle", "elastic"},
                  "easing": {"inout", "in", "out"}}


PARSER = ET.XMLParser(remove_blank_text=True, remove_comments=True)


class InfoProvider(object):

    def __init__(self):
        self.addon = None
        self.template_root = None
        self.WINDOW_FILENAMES = []
        self.WINDOW_NAMES = []
        self.WINDOW_IDS = []
        self.builtins = []
        self.conditions = []
        self.template_attribs = {}
        self.template_values = {}
        self.settings = {}
        self.kodi_path = None

    def load_data(self):
        """
        loads the xml with control nodes for sanity checking (controls.xml)
        as well as builtins including their help string (data.xml)
        """
        # TODO: clean this up
        kodi_version = "krypton"
        try:
            # since we get packaged we need to use load_resource() to load external files
            import sublime
            controls = sublime.load_resource("Packages/KodiDevKit/data/%s/controls.xml" % kodi_version)
            self.template_root = ET.fromstring(controls.encode("utf-8"), PARSER)
            # resolve includes
            data = sublime.load_resource("Packages/KodiDevKit/data/%s/data.xml" % kodi_version)
            root = ET.fromstring(data.encode("utf-8"), PARSER)
            WINDOW_MAP = json.loads(sublime.load_resource("Packages/KodiDevKit/data/%s/windows.json" % kodi_version))
        except Exception:
            # fallback to old method so that class still can get used without sublime import
            path = os.path.normpath(os.path.abspath(__file__))
            folder = os.path.split(path)[0]
            self.template_root = utils.get_root_from_file(os.path.join(folder, "..", "data", kodi_version, "controls.xml"))
            root = utils.get_root_from_file(os.path.join(folder, "..", "data", kodi_version, "data.xml"))
            with open(os.path.join(folder, "..", "data", kodi_version, "windows.json")) as f:
                WINDOW_MAP = json.load(f)
        self.WINDOW_FILENAMES = [item[2] for item in WINDOW_MAP]
        self.WINDOW_NAMES = [item[0] for item in WINDOW_MAP]
        self.WINDOW_IDS = [str(item[1]) for item in WINDOW_MAP]

        self.builtins = [[i.find("code").text, i.find("help").text] for i in root.find("builtins")]
        self.conditions = [[i.find("code").text, i.find("help").text] for i in root.find("conditions")]
        for include in self.template_root.xpath("//include[@name]"):
            for node in self.template_root.xpath("//include[not(@*)]"):
                if node.text == include.attrib.get("name"):
                    for child in include.getchildren():
                        child = copy.deepcopy(child)
                        node.getparent().append(child)
                    node.getparent().remove(node)
            self.template_root.remove(include)
        self.template_attribs = {}
        self.template_values = {}
        for template in self.template_root:
            self.template_attribs[template.attrib.get("type")] = {i.tag: i.attrib for i in template.iterchildren()}
            self.template_values[template.attrib.get("type")] = {i.tag: i.text for i in template.iterchildren()}

    def init_addon(self, path):
        """
        scan addon folder and parse skin content etc
        """
        self.addon = None
        addon_xml = os.path.join(path, "addon.xml")
        if os.path.exists(addon_xml):
            logging.info("Kodi project detected: " + addon_xml)
            self.addon = Addon.by_project(path, self.settings)
            # sublime.status_message("KodiDevKit: successfully loaded addon")

    def check_dependencies(self):
        """
        validate the addon dependencies
        """
        imports = {i.get('addon'): i.get('version') for i in self.addon.root.iter('import')}
        addons = []
        for release in self.addon.RELEASES:
            if self.addon.api_version == release["name"]:
                if imports['xbmc.gui'] > release["gui_version"]:
                    logging.info('xbmc.gui version incorrect')
                addons = utils.get_addons(release["name"])
                break
        else:
            logging.info('You entered an invalid Kodi version')
            return None
        del imports['xbmc.gui']
        for dep, ver in imports.items():
            if dep in addons:
                if ver > addons[dep]:
                    logging.info('%s version higher than in Kodi repository' % dep)
            else:
                logging.info('%s not available in Kodi repository' % dep)

    def get_check_listitems(self, check_type):
        """
        starts check with type check_type and returns result nodes
        """
        self.addon.update_xml_files()
        checks = {"variable": self.check_variables,
                  "include": self.check_includes,
                  "font": self.check_fonts,
                  "label": self.check_labels,
                  "id": self.check_ids,
                  "general": self.check_values}
        return checks[check_type]()

    def check_xml_files(self):
        """
        Checks if the skin contains all core xml window files
        """
        for folder in self.addon.xml_folders:
            for item in self.WINDOW_FILENAMES:
                if item not in self.addon.window_files[folder]:
                    logging.info("Skin does not include %s" % item)

    def go_to_tag(self, keyword, folder):
        """
        jumps to the definition of ref named keyword
        """
        # TODO: need to add param with ref type
        if not keyword:
            return False
        if keyword.isdigit():
            for po_file in self.get_po_files():
                for entry in po_file:
                    if entry.msgctxt == "#" + keyword:
                        return "%s:%s" % (po_file.fpath, entry.linenum)
        else:
            # TODO: need to check for include file attribute
            for node in self.addon.includes[folder]:
                if node["name"] == keyword:
                    return "%s:%s" % (node["file"], node["line"])
            for node in self.addon.fonts[folder]:
                if node["name"] == keyword:
                    path = os.path.join(self.addon.path, folder, "Font.xml")
                    return "%s:%s" % (path, node["line"])
            for node in self.get_colors():
                if node["name"] == keyword and node["file"].endswith(("defaults.xml", "colors.xml")):
                    return "%s:%s" % (node["file"], node["line"])
            logging.info("no node with name %s found" % keyword)
        return False

    def load_settings(self, settings):
        """
        load settings file
        """
        self.settings = settings
        self.kodi_path = settings.get("kodi_path")
        logging.info("kodi path: " + self.kodi_path)

    def return_label(self, selection):
        """
        return formatted label for id in *selection
        """
        tooltips = ""
        if not selection.isdigit():
            return ""
        for po_file in self.get_po_files():
            hit = po_file.find("#" + selection, by="msgctxt")
            if not hit:
                continue
            language = po_file.language.replace("resource.language.", "")
            tooltips += "<b>%s:</b> %s<br>" % (language, hit.msgstr if hit.msgstr else hit.msgid)
        return tooltips

    def get_po_files(self):
        """
        get list of all active po files
        """
        po_files = []
        if kodi.po_files:
            po_files.extend(kodi.po_files)
        if self.addon.po_files:
            po_files.extend(self.addon.po_files)
        return po_files

    def get_colors(self):
        """
        get list of all colors (core + addon)
        """
        colors = []
        if kodi.colors:
            colors.extend(kodi.colors)
        if self.addon.colors:
            colors.extend(self.addon.colors)
        return colors

    def get_color_labels(self):
        """
        get list of all color names (core + addon)
        """
        colors = self.get_colors()
        return {i["name"] for i in colors}

    def get_color_info_html(self, color_string):
        """
        return formatted info for *color_string, taken from color xmls (default + themes + core).
        """
        color_info = ""
        for item in self.get_colors():
            if item["name"] == color_string:
                color_hex = "#" + item["content"][2:]
                cont_color = utils.get_contrast_color(color_hex)
                alpha_percent = round(int(item["content"][:2], 16) / (16 * 16) * 100)
                color_info += '%s&nbsp;<a href="test" style="background-color:%s;color:%s">%s</a> %d %% alpha<br>' % (os.path.basename(item["file"]), color_hex, cont_color, item["content"], alpha_percent)
        if color_info:
            return color_info
        if all(c in string.hexdigits for c in color_string) and len(color_string) == 8:
            color_hex = "#" + color_string[2:]
            cont_color = utils.get_contrast_color(color_hex)
            alpha_percent = round(int(color_string[:2], 16) / (16 * 16) * 100)
            return '<a href="test" style="background-color:%s;color:%s">%d %% alpha</a>' % (color_hex, cont_color, alpha_percent)

    @staticmethod
    def get_ancestor_info(element):
        """
        iter through ancestors and return info about absolute position
        """
        values = {}
        for anc in element.iterancestors():
            for sib in anc.iterchildren():
                if sib.tag in POS_TAGS:
                    if sib.tag in values:
                        values[sib.tag].append(sib.text)
                    else:
                        values[sib.tag] = [sib.text]
        if not values:
            return ""
        anc_info = ["<b>{}:</b> {}".format(k, v) for k, v in values.items()]
        anc_info = "<br>".join(anc_info)
        return "<b>Absolute position</b><br>{}".format(anc_info)

    def check_variables(self):
        """
        return message listitems containing non-existing / unused variables
        """
        var_regex = r"\$(?:ESC)?VAR\[(.*?)\]"
        listitems = []
        for folder in self.addon.xml_folders:
            var_refs = []
            for xml_file in self.addon.window_files[folder]:
                path = os.path.join(self.addon.path, folder, xml_file)
                with open(path, encoding="utf8", errors="ignore") as f:
                    for i, line in enumerate(f.readlines()):
                        for match in re.finditer(var_regex, line):
                            item = {"line": i + 1,
                                    "type": "variable",
                                    "file": path,
                                    "name": match.group(1).split(",")[0]}
                            var_refs.append(item)
            for ref in var_refs:
                for node in self.addon.includes[folder]:
                    if node["type"] == "variable" and node["name"] == ref["name"]:
                        break
                else:
                    ref["message"] = "Variable not defined: %s" % ref["name"]
                    listitems.append(ref)
            ref_list = [d['name'] for d in var_refs]
            for node in self.addon.includes[folder]:
                if node["type"] == "variable" and node["name"] not in ref_list:
                    node["message"] = "Unused variable: %s" % node["name"]
                    listitems.append(node)
        return listitems

    def check_includes(self):
        """
        return message listitems for non-existing / unused includes
        """
        listitems = []
        # include check for each folder separately
        for folder in self.addon.xml_folders:
            var_refs = []
            # get all include refs
            for xml_file in self.addon.window_files[folder]:
                path = os.path.join(self.addon.path, folder, xml_file)
                root = utils.get_root_from_file(path)
                if root is None:
                    continue
                for node in root.xpath(".//include"):
                    if node.text and not node.text.startswith("skinshortcuts-"):
                        name = node.text
                        if "file" in node.attrib:
                            include_file = os.path.join(self.addon.path, folder, node.attrib["file"])
                            if include_file not in self.addon.include_files[folder]:
                                self.addon.update_includes(include_file)
                    elif node.attrib.get("content"):
                        name = node.attrib["content"]
                    else:
                        continue
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "file": path,
                            "name": name}
                    var_refs.append(item)
            # find undefined include refs
            for ref in var_refs:
                for node in self.addon.includes[folder]:
                    if node["type"] == "include" and node["name"] == ref["name"]:
                        break
                else:
                    if ref["name"].startswith("$"):
                        break
                    ref["message"] = "Include not defined: %s" % ref["name"]
                    listitems.append(ref)
            # find unused include defs
            ref_list = [d['name'] for d in var_refs]
            for node in self.addon.includes[folder]:
                if node["type"] == "include" and node["name"] not in ref_list:
                    node["message"] = "Unused include: %s" % node["name"]
                    listitems.append(node)
        return listitems

    def build_translate_label(self, label_id, view):
        """
        return correctly formatted translate label based on context
        """
        scope_name = view.scope_name(view.sel()[0].b)
        # TODO: blank string for settings.xml
        if "text.xml" in scope_name and self.addon.type == "python" and 32000 <= label_id <= 33000:
            return "$ADDON[%s %i]" % (self.addon.name, label_id)
        elif "text.xml" in scope_name:
            return "$LOCALIZE[%i]" % label_id
        elif "source.python" in scope_name and 32000 <= label_id <= 33000:
            return "ADDON.getLocalizedString(%i)" % label_id
        elif "source.python" in scope_name:
            return "xbmc.getLocalizedString(%i)" % label_id
        else:
            return str(label_id)

    def get_image_info(self, path):
        """
        return correctly formatted translate label based on context
        """
        imagepath = self.addon.translate_path(path)
        if not os.path.exists(imagepath) or os.path.isdir(imagepath):
            return ""
        info = imageparser.get_image_info(imagepath)
        text = ["<b>%s</b>: %s" % (k, v) for k, v in info]
        return "<br>".join(text)

    def check_fonts(self):
        """
        check for undefined and unused fonts and return a list of message dicts
        """
        listitems = []
        font_refs = self.addon.get_font_refs()
        # get estuary fonts..
        estuary_fonts = []
        estuary_font_file = os.path.join(self.kodi_path, "addons", "skin.estuary", "xml", "Font.xml")
        root = utils.get_root_from_file(estuary_font_file)
        if root is not None:
            estuary_fonts = [node.find("name").text for node in root.find("fontset").findall("font")]
            # check fonts from each folder independently....
        for folder in self.addon.xml_folders:
            fontlist = [""]
            # create a list with all font names from default fontset
            if folder in self.addon.fonts:
                for item in self.addon.fonts[folder]:
                    fontlist.append(item["name"])
            # find undefined font refs
            for ref in font_refs[folder]:
                if ref["name"].startswith("$PARAM"):
                    continue
                if ref["name"] not in fontlist + estuary_fonts:
                    ref["message"] = "Font not defined: %s" % ref["name"]
                    listitems.append(ref)
            # find unused font defs
            ref_list = [d['name'] for d in font_refs[folder]]
            if folder in self.addon.fonts:
                for node in self.addon.fonts[folder]:
                    if node["name"] not in ref_list + estuary_fonts:
                        node["message"] = "Unused font: %s" % node["name"]
                        listitems.append(node)
        return listitems

    def check_ids(self):
        """
        check for undefined and invalid control / message ids and return a list of message dicts
        """
        window_regex = r"(?:Dialog.Close|Window.IsActive|Window.IsVisible|Window)\(([0-9]+)\)"
        control_regex = r"^(?!.*IsActive)(?!.*Window.IsVisible)(?!.*Dialog.Close)(?!.*Window)(?!.*Row)(?!.*Column).*\(([0-9]*?)\)"
        listitems = []
        for folder in self.addon.xml_folders:
            window_ids = []
            window_refs = []
            control_refs = []
            defines = []
            for xml_file in self.addon.window_files[folder]:
                path = os.path.join(self.addon.path, folder, xml_file)
                root = utils.get_root_from_file(path)
                if root is None:
                    continue
                if "id" in root.attrib:
                    window_ids.append(root.attrib["id"])
                # get all nodes with ids....
                for node in root.xpath(".//*[@id]"):
                    item = {"name": node.attrib["id"],
                            "type": node.tag,
                            "file": path,
                            "line": node.sourceline}
                    defines.append(item)
                # get all conditions....
                for node in root.xpath(".//*[@condition]"):
                    for match in re.finditer(control_regex, node.attrib["condition"], re.IGNORECASE):
                        item = {"name": match.group(1),
                                # "region": (match.start(1), match.end(1)),
                                "type": node.tag,
                                "file": path,
                                "line": node.sourceline}
                        control_refs.append(item)
                    for match in re.finditer(window_regex, node.attrib["condition"], re.IGNORECASE):
                        item = {"name": match.group(1),
                                "type": node.tag,
                                "file": path,
                                "line": node.sourceline}
                        window_refs.append(item)
                bracket_tags = ["visible", "enable", "usealttexture", "selected", "onclick", "onback"]
                for node in root.xpath(".//" + " | .//".join(bracket_tags)):
                    if not node.text:
                        continue
                    for match in re.finditer(control_regex, node.text, re.IGNORECASE):
                        item = {"name": match.group(1),
                                "type": node.tag,
                                "file": path,
                                "line": node.sourceline}
                        control_refs.append(item)
                    for match in re.finditer(window_regex, node.text, re.IGNORECASE):
                        item = {"name": match.group(1),
                                "type": node.tag,
                                "file": path,
                                "line": node.sourceline}
                        window_refs.append(item)
                # check if all refs exist...
            define_list = [d['name'] for d in defines]
            for item in window_refs:
                if item["name"] in window_ids:
                    pass
                elif item["name"] in self.WINDOW_IDS:
                    windowname = self.WINDOW_NAMES[self.WINDOW_IDS.index(item["name"])]
                    item["message"] = "Window id: Please use %s instead of %s" % (windowname, item["name"])
                    listitems.append(item)
                else:
                    item["message"] = "Window ID not defined: " + item["name"]
                    listitems.append(item)
            for item in control_refs:
                if not item["name"] or item["name"] in define_list:
                    continue
                item["message"] = "Control / Item ID not defined: " + item["name"]
                listitems.append(item)
        return listitems

    def check_labels(self):
        """
        check for untranslated / undefined labels and return a list of message dicts
        """
        listitems = []
        refs = []
        localize_regex = [r"\$LOCALIZE\[([0-9].*?)\]", r"^(\d+)$"]
        # labels = [s.msgid for s in self.po_files]
        checks = [[".//viewtype[(@label)]", "label"],
                  [".//fontset[(@idloc)]", "idloc"],
                  [".//label[(@fallback)] | .//label2[(@fallback)]", "fallback"]]
        for folder in self.addon.xml_folders:
            for xml_file in self.addon.window_files[folder]:
                path = os.path.join(self.addon.path, folder, xml_file)
                root = utils.get_root_from_file(path)
                if root is None:
                    continue
                # find all referenced label ids (in element content)
                for element in root.xpath(".//label | .//altlabel | .//label2 | .//hinttext"):
                    if not element.text:
                        continue
                    for match in re.finditer(localize_regex[0], element.text):
                        item = {"name": match.group(1),
                                "type": element.tag,
                                "file": path,
                                "line": element.sourceline}
                        refs.append(item)
                    if element.text.isdigit():
                        item = {"name": element.text,
                                "type": element.tag,
                                "file": path,
                                "line": element.sourceline}
                        refs.append(item)
                # check for untranslated strings...
                    elif len(element.text.strip()) > 1 and not element.text.endswith(".xml") and element.text.strip()[0].isalpha():
                        item = {"name": element.text,
                                "type": element.tag,
                                "file": path,
                                "identifier": element.text,
                                "message": "Label in <%s> not translated: %s" % (element.tag, element.text),
                                "line": element.sourceline}
                        listitems.append(item)
                # find some more references (in attribute values this time)....
                for check in checks:
                    for element in root.xpath(check[0]):
                        attr = element.attrib[check[1]]
                        for regex in localize_regex:
                            for match in re.finditer(regex, attr):
                                item = {"name": match.group(1),
                                        "type": element.tag,
                                        "file": path,
                                        "line": element.sourceline}
                                refs.append(item)
                        # find some more untranslated strings
                        if not attr.isdigit() and len(attr.strip()) > 1 and attr.strip()[0].isalpha():
                            item = {"name": attr,
                                    "type": element.tag,
                                    "file": path,
                                    "identifier": attr,
                                    "message": 'Label in attribute %s not translated: %s' % (check[1], attr),
                                    "line": element.sourceline}
                            listitems.append(item)
        # check if refs are defined in po files
        label_ids = []
        for po_file in self.get_po_files():
            label_ids += [entry.msgctxt for entry in po_file]
        for ref in refs:
            if "#" + ref["name"] not in label_ids:
                ref["message"] = "Label not defined: %s" % ref["name"]
                listitems.append(ref)
        return listitems

    def check_values(self):
        """
        apply check_file to all our xmls, return resulting list of message dicts
        """
        listitems = []
        for path in self.addon.get_xml_files():
            new_items = self.check_file(path)
            listitems.extend(new_items)
        return listitems

    def check_file(self, path):
        """
        check xml file with *path for common errors and return a list of message dicts
        """
        # tags allowed for all controls
        root = utils.get_root_from_file(path)
        if root is None:
            return []
        folder = path.split(os.sep)[-2]
        tree = ET.ElementTree(root)
        listitems = []
        xpath = " or ".join(["lower-case(string(@type))='{}'".format(c) for c in self.template_attribs])
        xpath = ".//control[not({}) and @type[string()]]".format(xpath)
        for node in root.xpath(xpath):
            if node.attrib.get("type").startswith("$PARAM["):
                pass
            item = {"line": node.sourceline,
                    "type": node.tag,
                    "identifier": node.attrib.get("type"),
                    "message": "invalid control type: %s" % (node.attrib.get("type"))}
            listitems.append(item)
        for c_type, subnodes, node, subnode in self.file_control_checks(root):
            if subnode.tag not in subnodes:
                label = node.tag if "type" not in node.attrib else "%s type=%s" % (node.tag, node.attrib.get("type"))
                item = {"line": subnode.sourceline,
                        "type": subnode.tag,
                        "identifier": subnode.tag,
                        "message": "invalid tag for <%s>: <%s>" % (label, subnode.tag)}
                listitems.append(item)
                continue
            if self.template_values[c_type][subnode.tag] in ALLOWED_VALUES:
                if subnode.text.lower() not in ALLOWED_VALUES[self.template_values[c_type][subnode.tag]] and not subnode.text.startswith("$PARAM["):
                    item = {"line": subnode.sourceline,
                            "type": subnode.tag,
                            "identifier": subnode.text,
                            "message": "invalid value for %s: %s" % (subnode.tag, subnode.text)}
                    listitems.append(item)
            if subnode.tag in NOOP_TAGS:
                if not subnode.text or not subnode.text != "-":
                    item = {"line": subnode.sourceline,
                            "type": subnode.tag,
                            "identifier": subnode.tag,
                            "message": "Use 'noop' for empty calls <%s>" % (node.tag)}
                    listitems.append(item)
            if subnode.tag in BRACKET_TAGS:
                if not subnode.text:
                    item = {"line": subnode.sourceline,
                            "type": subnode.tag,
                            "identifier": "",
                            "message": "Empty condition: %s" % (subnode.tag)}
                    listitems.append(item)
                elif not utils.check_brackets(subnode.text):
                    condition = str(subnode.text).replace("  ", "").replace("\t", "")
                    item = {"line": subnode.sourceline,
                            "type": subnode.tag,
                            "identifier": condition,
                            "message": "Brackets do not match: %s" % (condition)}
                    listitems.append(item)
            if subnode.tag in DOUBLE_TAGS and not subnode.getchildren():
                xpath = tree.getpath(subnode)
                if xpath.endswith("]") and not xpath.endswith("[1]"):
                    item = {"line": subnode.sourceline,
                            "type": subnode.tag,
                            "identifier": subnode.tag,
                            "message": "Invalid multiple tags for %s: <%s>" % (subnode.getparent().tag, subnode.tag)}
                    listitems.append(item)
            for k, v in subnode.attrib.items():
                if k == "description":
                    continue
                if k not in subnodes[subnode.tag]:
                    item = {"line": subnode.sourceline,
                            "type": subnode.tag,
                            "identifier": k,
                            "message": "invalid attribute for <%s>: %s" % (subnode.tag, k)}
                    listitems.append(item)
                    continue
                elif "$PARAM[" in v or "$VAR[" in v:
                    continue
                value_type = subnodes[subnode.tag][k]
                if value_type == "int":
                    if not utils.is_number(v) and v not in self.addon.get_constants(folder):
                        item = {"line": subnode.sourceline,
                                "type": subnode.tag,
                                "identifier": v,
                                "message": "invalid integer value for %s: %s" % (k, v)}
                        listitems.append(item)
                elif value_type == "color":
                    if v not in self.get_color_labels() and not utils.is_kodi_hex(v) and not v.startswith("$"):
                        item = {"line": subnode.sourceline,
                                "type": subnode.tag,
                                "identifier": v,
                                "message": "Invalid color for %s: %s" % (k, v)}
                        listitems.append(item)
                elif value_type in ALLOWED_VALUES:
                    if v not in ALLOWED_VALUES[value_type.lower()] and not v.startswith("$PARAM["):
                        item = {"line": subnode.sourceline,
                                "type": subnode.tag,
                                "identifier": v,
                                "message": "invalid value for %s attribute: %s" % (k, v)}
                        listitems.append(item)
                if k == "condition" and not utils.check_brackets(subnode.attrib["condition"]):
                    condition = str(v).replace("  ", "").replace("\t", "")
                    item = {"line": subnode.sourceline,
                            "type": subnode.tag,
                            "identifier": condition,
                            "message": "Brackets do not match: %s" % (condition)}
                    listitems.append(item)
        for item in listitems:
            item["filename"] = os.path.basename(path)
            item["file"] = path
        return listitems

    def file_control_checks(self, root):
        """
        compare controls with our templates
        """
        for c_type, subnodes in self.template_attribs.items():
            for node in root.xpath(".//control[lower-case(string(@type))='%s']" % c_type):
                for subnode in node.iterchildren():
                    yield (c_type, subnodes, node, subnode)
