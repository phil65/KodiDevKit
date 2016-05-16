# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
KodiDevKit is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""


import sublime_plugin
import sublime

import time
import re
import os
import webbrowser
import logging
from itertools import chain
from xml.sax.saxutils import escape

import mdpopups

from .libs import Utils
from .libs import sublimelogger
from .libs import infoprovider
from .libs.kodi import kodi

INFOS = infoprovider.InfoProvider()
# sublime.log_commands(True)
SETTINGS_FILE = 'kodidevkit.sublime-settings'

sublimelogger.config()


def plugin_loaded():
    """
    ST API method: gets called once API is ready
    """
    settings = sublime.load_settings(SETTINGS_FILE)
    kodi.load_settings(settings)
    INFOS.load_settings(settings)
    INFOS.load_data()
    KodiDevKit.settings = settings


class KodiDevKit(sublime_plugin.EventListener):

    """
    Handles interaction of ST with InfoProviders (kodi/skin)
    """

    def __init__(self, **kwargs):
        self.actual_project = None
        self.prev_selection = None
        self.is_modified = False

    def on_query_completions(self, view, prefix, locations):
        """
        ST API method: gets called when autocompletion triggers
        """
        completions = []
        scope_name = view.scope_name(view.sel()[0].b)
        filename = view.file_name()
        if not filename or not INFOS.addon:
            return []
        folder = filename.split(os.sep)[-2]
        if folder not in INFOS.addon.includes:
            return []
        if "text.xml" in scope_name:
            colors = []
            for node in INFOS.addon.colors:
                if node["name"] not in colors:
                    colors.append(node["name"])
                    completions.append(["%s (%s)" % (node["name"], node["content"]), node["name"]])
            for node in chain(INFOS.addon.includes[folder], INFOS.addon.fonts[folder]):
                completions.append([node["name"], node["name"]])
            for node in chain(INFOS.builtins, INFOS.conditions):
                completions.append([node[0], node[0]])
            for item in infoprovider.WINDOW_NAMES:
                completions.append([item, item])
            for item in completions:
                for i, match in enumerate(re.findall(r"\([a-z,\]\[]+\)", item[1])):
                    item[1] = item[1].replace(match, "($%i)" % (i + 1))
            return completions.sort()
            # return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

    def on_selection_modified_async(self, view):
        """
        ST API method: gets called when selection changed
        """
        if len(view.sel()) > 1 or not INFOS.addon:
            return None
        try:
            region = view.sel()[0]
            folder = view.file_name().split(os.sep)[-2]
        except Exception:
            return None
        if region == self.prev_selection:
            return None
        self.prev_selection = region
        view.hide_popup()
        tooltip = self.get_tooltip(view, region, folder)

        # node = INFOS.template_root.find(".//control[@type='label']")
        # logging.info(node)
        # popup_label = node.find(".//available_tags").text.replace("\\n", "<br>")
        if tooltip and self.settings.get("tooltip_delay", 0) > -1:
            sublime.set_timeout_async(lambda: self.show_tooltip(view, tooltip),
                                      self.settings.get("tooltip_delay", 0))

    def get_tooltip(self, view, region, folder):
        """
        get correct tooltip based on context (veeery hacky atm)
        """
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        info_type = ""
        info_id = ""
        scope_name = view.scope_name(region.b)
        scope_content = view.substr(view.extract_scope(region.b))
        line = view.line(region)
        line_contents = view.substr(line).lower().strip()
        label_region = view.expand_by_class(region, flags, '$],')
        bracket_region = view.expand_by_class(region, flags, '<>')
        selected_content = view.substr(view.expand_by_class(region, flags, '<>"[]'))
        if label_region.begin() > bracket_region.begin() and label_region.end() < bracket_region.end():
            info_list = view.substr(label_region).split("[", 1)
            info_type = info_list[0]
            if len(info_list) > 1:
                info_id = info_list[1]
        if "source.python" in scope_name:
            if "lang" in line_contents or "label" in line_contents or "string" in line_contents:
                word = view.substr(view.word(region))
                text = INFOS.return_label(word)
                if text:
                    return text
        elif "text.xml" in scope_name:
            if info_type in ["VAR", "ESCVAR", "EXP"]:
                node = INFOS.addon.return_node(info_id, folder=folder)
                if node["content"]:
                    return mdpopups.syntax_highlight(view=view,
                                                     src=node["content"],
                                                     language="xml")
            elif info_type in ["INFO", "ESCINFO"]:
                result = kodi.request(method="XBMC.GetInfoLabels",
                                      params={"labels": [info_id]})
                if result:
                    _, value = result["result"].popitem()
                    if value:
                        return str(value)
            elif info_type == "LOCALIZE":
                return INFOS.return_label(info_id)
            if line_contents.startswith(("<include>", "<include content=", "<font", "<depth")):
                content = Utils.get_node_content(view, flags)
                node = INFOS.addon.return_node(content, folder=folder)
                if node:
                    node_content = str(node["content"])
                    if not node_content:
                        pass
                    elif len(node_content) < 10000:
                        return mdpopups.syntax_highlight(view=view,
                                                         src=node_content,
                                                         language="xml")
                    else:
                        return "include too big for preview"
            elif "<visible" in line_contents or "<enable" in line_contents:
                self.boolean_popup(selected_content, view)
            elif "label" in line_contents or "<property" in line_contents or "localize" in line_contents:
                label = INFOS.return_label(selected_content)
                if label:
                    return label
            elif "<fadetime" in line_contents:
                content = Utils.get_node_content(view, flags)
                node = INFOS.addon.return_node(content, folder=folder)
                node_content = str(node["content"])[2:-3]
            elif line_contents.startswith(("<texture", "<alttexture", "<bordertexture", "<icon", "<thumb")):
                return INFOS.get_image_info(selected_content)
            elif "<control " in line_contents:
                # TODO: add positioning based on parent nodes
                line, _ = view.rowcol(view.sel()[0].b)
                return INFOS.get_ancestor_info(view.file_name(), line)
            color = INFOS.addon.get_color_info(selected_content)
            if color:
                return color
            if "constant.other.allcaps" in scope_name:
                window_name = scope_content.lower()[1:-1]
                if window_name in infoprovider.WINDOW_NAMES:
                    window_index = infoprovider.WINDOW_NAMES.index(window_name)
                    return infoprovider.WINDOW_FILENAMES[window_index]

    @Utils.run_async
    def boolean_popup(self, selected_content, view):
        """
        popup to show boolean value
        """
        result = kodi.request(method="XBMC.GetInfoBooleans",
                              params={"booleans": [selected_content]})
        if result:
            _, value = result["result"].popitem()
            if value is not None:
                sublime.set_timeout_async(lambda: self.show_tooltip(view, str(value)),
                                          self.settings.get("tooltip_delay", 0))

    def show_tooltip(self, view, tooltip_label):
        """
        show tooltip using mdpopups
        """
        mdpopups.show_popup(view=view,
                            content=tooltip_label,
                            flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                            max_width=self.settings.get("tooltip_width", 1000),
                            max_height=self.settings.get("height", 400),
                            on_navigate=lambda label_id, view=view: Utils.jump_to_label_declaration(view, tooltip_label))

    def on_modified_async(self, view):
        if INFOS.addon and INFOS.addon.path:
            if view.file_name() and view.file_name().endswith(".xml"):
                self.is_modified = True

    def on_load_async(self, view):
        self.check_status()

    def on_activated_async(self, view):
        self.check_status()

    def on_deactivated_async(self, view):
        view.hide_popup()

    def on_post_save_async(self, view):
        if not INFOS.addon or not view.file_name():
            return False
        if view.file_name().endswith(".xml"):
            if not self.is_modified:
                return False
            INFOS.addon.update_xml_files()
            filename = os.path.basename(view.file_name())
            folder = view.file_name().split(os.sep)[-2]
            INFOS.addon.reload_after_save(view.file_name())
            if folder in INFOS.addon.window_files and filename in INFOS.addon.window_files[folder]:
                if self.settings.get("auto_reload_skin", True):
                    self.is_modified = False
                    view.window().run_command("execute_builtin",
                                              {"builtin": "ReloadSkin()"})
                if self.settings.get("auto_skin_check", True):
                    view.window().run_command("check_variables",
                                              {"check_type": "file"})
        if view.file_name().endswith(".po"):
            INFOS.addon.update_labels()

    def check_status(self):
        """
        check currently visible view, assign syntax file and update InfoProvider if needed
        """
        view = sublime.active_window().active_view()
        filename = view.file_name()
        if INFOS.addon and filename and filename.endswith(".xml"):
            view.assign_syntax('Packages/KodiDevKit/KodiSkinXML.sublime-syntax')
        if filename and filename.endswith(".po"):
            view.assign_syntax('Packages/KodiDevKit/Gettext.tmLanguage')
        if filename and filename.endswith(".log"):
            view.assign_syntax('Packages/KodiDevKit/KodiLog.sublime-syntax')
        if view and view.window() is not None:
            variables = view.window().extract_variables()
            if "folder" in variables:
                project_folder = variables["folder"]
                if project_folder and project_folder != self.actual_project:
                    self.actual_project = project_folder
                    logging.info("project change detected: " + project_folder)
                    INFOS.init_addon(project_folder)
            else:
                logging.info("Could not find folder path in project file")


class ReloadKodiLanguageFilesCommand(sublime_plugin.WindowCommand):

    """
    Command to manually reload language files
    """

    def run(self):
        INFOS.load_settings(sublime.load_settings(SETTINGS_FILE))
        kodi.update_labels()
        INFOS.addon.update_labels()


class QuickPanelCommand(sublime_plugin.WindowCommand):

    """
    Parent class including method callbacks to show location and select text
    """

    def is_visible(self):
        return bool(INFOS.addon)

    def on_done(self, index):
        if index == -1:
            return None
        node = self.nodes[index]
        view = self.window.open_file("%s:%i" % (node["file"], node["line"]),
                                     sublime.ENCODED_POSITION)
        self.select_text(view, node)

    def show_preview(self, index):
        node = self.nodes[index]
        self.window.open_file("%s:%i" % (node["file"], node["line"]),
                              sublime.ENCODED_POSITION | sublime.TRANSIENT)

    @Utils.run_async
    def select_text(self, view, node):
        while view.is_loading():
            time.sleep(0.01)
        view.sel().clear()
        if "identifier" in node:
            text_point = view.text_point(node["line"] - 1, 0)
            label = escape(node["identifier"])
            line_contents = view.substr(view.line(text_point))
            if line_contents.count(label) != 1:
                return False
            line_start = line_contents.find(label)
            line_end = line_start + len(label)
            view.sel().add(sublime.Region(text_point + line_start, text_point + line_end))


class OpenSkinImageCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        return bool(INFOS.addon) and os.path.exists(INFOS.addon.media_path)

    @Utils.run_async
    def run(self, pack_textures=True):
        view = self.window.active_view()
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        path = Utils.get_node_content(view, flags)
        imagepath = INFOS.addon.translate_path(path)
        if not os.path.exists(imagepath):
            return None
        webbrowser.open(imagepath)


class BuildAddonCommand(sublime_plugin.WindowCommand):

    """
    Create an installable zip archive of the currently open addon
    """

    def is_visible(self):
        return bool(INFOS.addon) and INFOS.addon.type == "skin"

    @Utils.run_async
    def run(self, pack_textures=True):
        path = INFOS.addon.media_path
        Utils.texturepacker(media_path=path,
                            settings=sublime.load_settings(SETTINGS_FILE))
        Utils.make_archive(folderpath=path,
                           archive=os.path.join(path, os.path.basename(path) + ".zip"))
        if sublime.ok_cancel_dialog("Zip file created!\nDo you want to show it with a file browser?"):
            webbrowser.open(path)


class BuildThemeCommand(sublime_plugin.WindowCommand):

    """
    Select and build a theme of the currently open skin
    """

    def is_visible(self):
        return bool(INFOS.addon) and os.path.exists(INFOS.addon.theme_path)

    def run(self, pack_textures=True):
        self.themes = INFOS.addon.get_themes()
        self.window.show_quick_panel(items=self.themes,
                                     on_select=self.on_done,
                                     selected_index=0)

    @Utils.run_async
    def on_done(self, index):
        if index == -1:
            return None
        media_path = os.path.join(INFOS.addon.theme_path, self.themes[index])
        Utils.texturepacker(media_path=media_path,
                            settings=sublime.load_settings(SETTINGS_FILE),
                            xbt_filename=self.themes[index] + ".xbt")
        if sublime.ok_cancel_dialog("Theme file created!\nDo you want to show it with a file browser?"):
            webbrowser.open(media_path)


class ShowFontRefsCommand(QuickPanelCommand):

    def run(self):
        listitems = []
        self.nodes = []
        view = self.window.active_view()
        font_refs = INFOS.addon.get_font_refs()
        self.folder = view.file_name().split(os.sep)[-2]
        self.nodes = [ref for ref in font_refs[self.folder] if ref["name"] == "Font_Reg28"]
        listitems = [i["name"] for i in self.nodes]
        if listitems:
            self.window.show_quick_panel(items=listitems,
                                         on_select=self.on_done,
                                         selected_index=0,
                                         on_highlight=self.show_preview)
        else:
            logging.critical("No references found")


class SearchFileForLabelsCommand(QuickPanelCommand):

    def run(self):
        listitems = []
        self.nodes = []
        labels = []
        label_ids = []
        regexs = [r"\$LOCALIZE\[([0-9].*?)\]",
                  r"\$ADDON\[.*?([0-9].*?)\]",
                  r"(?:label|property|altlabel|label2)>([0-9].*?)<"]
        path = self.window.active_view().file_name()
        for po_file in INFOS.get_po_files():
            labels += [s.msgid for s in po_file]
            label_ids += [s.msgctxt for s in po_file]
        with open(path, encoding="utf8") as f:
            for i, line in enumerate(f.readlines()):
                for regex in regexs:
                    for match in re.finditer(regex, line):
                        label_id = "#" + match.group(1)
                        if label_id in label_ids:
                            index = label_ids.index(label_id)
                            listitems.append("%s (%s)" % (labels[index], label_id))
                        node = {"file": path,
                                "line": i + 1}
                        self.nodes.append(node)
        if listitems:
            self.window.show_quick_panel(items=listitems,
                                         on_select=self.on_done,
                                         selected_index=0,
                                         on_highlight=self.show_preview)
        else:
            logging.critical("No references found")


class CheckVariablesCommand(QuickPanelCommand):

    def run(self, check_type):
        if check_type == "file":
            filename = self.window.active_view().file_name()
            self.nodes = INFOS.check_file(filename)
        else:
            self.nodes = INFOS.get_check_listitems(check_type)
        listitems = [[i["message"], "%s: %s" % (os.path.basename(i["file"]), i["line"])] for i in self.nodes]
        if listitems:
            self.window.show_quick_panel(items=listitems,
                                         on_select=self.on_done,
                                         selected_index=0,
                                         on_highlight=self.show_preview)
        elif not check_type == "file":
            logging.critical("No errors detected")


class OpenActiveWindowXmlFromRemoteCommand(sublime_plugin.WindowCommand):

    """
    checks currently active window via JSON and opens corresponding XML file
    """

    @Utils.run_async
    def run(self):
        folder = self.window.active_view().file_name().split(os.sep)[-2]
        result = kodi.request(method="XBMC.GetInfoLabels",
                              params={"labels": ["Window.Property(xmlfile)"]})
        if not result:
            return None
        _, value = result["result"].popitem()
        if os.path.exists(value):
            self.window.open_file(value)
        for xml_file in INFOS.addon.window_files[folder]:
            if xml_file == value:
                path = os.path.join(INFOS.addon.path, folder, xml_file)
                self.window.open_file(path)
                return None


class SearchForLabelCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        return bool(INFOS.addon) and bool(INFOS.get_po_files())

    def run(self):
        listitems = []
        self.ids = []
        for po_file in INFOS.get_po_files():
            for entry in po_file:
                if entry.msgctxt not in self.ids:
                    self.ids.append(entry.msgctxt)
                    listitems.append(["%s (%s)" % (entry.msgid, entry.msgctxt), entry.comment])
        self.window.show_quick_panel(items=listitems,
                                     on_select=self.label_search_ondone_action,
                                     selected_index=0)

    def label_search_ondone_action(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        label_id = int(self.ids[index][1:])
        view.run_command("insert",
                         {"characters": INFOS.build_translate_label(label_id, view)})


class SearchForBuiltinCommand(sublime_plugin.WindowCommand):

    def run(self):
        listitems = [["%s" % (item[0]), item[1]] for item in INFOS.builtins]
        self.window.show_quick_panel(items=listitems,
                                     on_select=self.builtin_search_on_done,
                                     selected_index=0)

    def builtin_search_on_done(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        view.run_command("insert", {"characters": INFOS.builtins[index][0]})


class BumpVersionCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_quick_panel(items=["Major", "Minor", "Bugfix"],
                                     on_select=self.on_done,
                                     selected_index=0)

    def on_done(self, index):
        if index == -1:
            return None
        INFOS.addon.bump_version("9.9.9")
        self.window.open_file(INFOS.addon.changelog_path)


class SearchForVisibleConditionCommand(sublime_plugin.WindowCommand):

    def run(self):
        listitems = [["%s" % (item[0]), item[1]] for item in INFOS.conditions]
        self.window.show_quick_panel(items=listitems,
                                     on_select=self.builtin_search_on_done,
                                     selected_index=0)

    def builtin_search_on_done(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        view.run_command("insert", {"characters": INFOS.conditions[index][0]})


class SearchForJsonCommand(sublime_plugin.WindowCommand):

    @Utils.run_async
    def run(self):
        result = kodi.request(method="JSONRPC.Introspect")
        self.listitems = [[k, str(v)] for k, v in result["result"]["types"].items()]
        self.listitems += [[k, str(v)] for k, v in result["result"]["methods"].items()]
        self.listitems += [[k, str(v)] for k, v in result["result"]["notifications"].items()]
        self.window.show_quick_panel(items=self.listitems,
                                     on_select=self.builtin_search_on_done,
                                     selected_index=0)

    def builtin_search_on_done(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        view.run_command("insert", {"characters": str(self.listitems[index][0])})


class PreviewImageCommand(sublime_plugin.TextCommand):

    """
    show image preview of selected text inside SublimeText
    """

    def is_visible(self):
        if not INFOS.addon or not INFOS.addon.media_path:
            return False
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        content = Utils.get_node_content(self.view, flags)
        return "/" in content or "\\" in content

    def run(self, edit):
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        path = Utils.get_node_content(self.view, flags)
        imagepath = INFOS.addon.translate_path(path)
        if not os.path.exists(imagepath):
            return None
        if os.path.isdir(imagepath):
            self.files = []
            for (_, __, filenames) in os.walk(imagepath):
                self.files.extend(filenames)
                break
            self.files = [imagepath + s for s in self.files]
        else:
            self.files = [imagepath]
        sublime.active_window().show_quick_panel(items=self.files,
                                                 on_select=self.on_done,
                                                 selected_index=0,
                                                 on_highlight=self.show_preview)

    def on_done(self, index):
        sublime.active_window().focus_view(self.view)

    def show_preview(self, index):
        if index >= 0:
            file_path = self.files[index]
            sublime.active_window().open_file(file_path, sublime.TRANSIENT)


class GoToTagCommand(sublime_plugin.WindowCommand):

    """
    Jump to include/font/etc
    """

    def run(self):
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        view = self.window.active_view()
        position = INFOS.go_to_tag(keyword=Utils.get_node_content(view, flags),
                                   folder=view.file_name().split(os.sep)[-2])
        if position:
            self.window.open_file(position, sublime.ENCODED_POSITION)


class SearchForImageCommand(sublime_plugin.TextCommand):

    """
    Search through all files in media folder via QuickPanel
    """

    def is_visible(self):
        return bool(INFOS.addon and INFOS.addon.media_path)

    def run(self, edit):
        self.files = [i for i in INFOS.addon.get_media_files()]
        sublime.active_window().show_quick_panel(items=self.files,
                                                 on_select=self.on_done,
                                                 selected_index=0,
                                                 on_highlight=self.show_preview)

    def on_done(self, index):
        items = ["Insert path", "Open Image"]
        if index >= 0:
            sublime.active_window().show_quick_panel(items=items,
                                                     on_select=lambda s: self.insert_char(s, index),
                                                     selected_index=0)
        else:
            sublime.active_window().focus_view(self.view)

    def insert_char(self, index, fileindex):
        if index == 0:
            self.view.run_command("insert", {"characters": self.files[fileindex]})
        elif index == 1:
            os.system("start " + os.path.join(INFOS.addon.media_path, self.files[fileindex]))
        sublime.active_window().focus_view(self.view)

    def show_preview(self, index):
        if index >= 0:
            file_path = os.path.join(INFOS.addon.media_path, self.files[index])
        sublime.active_window().open_file(file_path, sublime.TRANSIENT)


class SearchForFontCommand(sublime_plugin.TextCommand):

    """
    search through all fonts from Fonts.xml via QuickPanel
    """

    def is_visible(self):
        return bool(INFOS.addon and INFOS.addon.fonts)

    def run(self, edit):
        self.fonts = []
        folder = self.view.file_name().split(os.sep)[-2]
        self.fonts = [[i["name"], "%s  -  %s" % (i["size"], i["filename"])] for i in INFOS.addon.fonts[folder]]
        sublime.active_window().show_quick_panel(items=self.fonts,
                                                 on_select=self.on_done,
                                                 selected_index=0)

    def on_done(self, index):
        if index >= 0:
            self.view.run_command("insert", {"characters": self.fonts[index][0]})
        sublime.active_window().focus_view(self.view)


class MoveToLanguageFile(sublime_plugin.TextCommand):

    """
    move selected file to default .po file (or create .po file if not existing)
    """

    def is_visible(self):
        scope_name = self.view.scope_name(self.view.sel()[0].b)
        if INFOS.addon and INFOS.addon.po_files:
            if "text.xml" in scope_name or "source.python" in scope_name:
                return self.view.sel()[0].b != self.view.sel()[0].a
        return False

    def run(self, edit):
        self.label_ids = []
        self.labels = []
        region = self.view.sel()[0]
        if region.begin() == region.end():
            logging.critical("Please select the complete label")
            return False
        word = self.view.substr(region)
        for po_file in INFOS.get_po_files():
            for entry in po_file:
                if entry.msgid.lower() == word.lower() and entry.msgctxt not in self.label_ids:
                    self.label_ids.append(entry.msgctxt)
                    self.labels.append(["%s (%s)" % (entry.msgid, entry.msgctxt), entry.comment])
        self.labels.append("Create new label")
        sublime.active_window().show_quick_panel(items=self.labels,
                                                 on_select=lambda s: self.on_done(s, region),
                                                 selected_index=0)

    def on_done(self, index, region):
        if index == -1:
            return None
        region = self.view.sel()[0]
        rel_path = self.view.file_name().replace(INFOS.addon.path, "").replace("\\", "/")
        if self.labels[index] == "Create new label":
            label_id = INFOS.addon.create_new_label(word=self.view.substr(region),
                                                    filepath=rel_path)
        else:
            label_id = self.label_ids[index]
            if 31000 <= int(label_id[1:]) < 33000:
                entry = INFOS.addon.po_files[0].find(label_id, by="msgctxt")
                entry.occurrences.append((rel_path, None))
                INFOS.addon.po_files[0].save(INFOS.addon_po_files[0].fpath)
        self.view.run_command("replace_text", {"label_id": label_id})


class ReplaceTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, label_id):
        for region in self.view.sel():
            new = INFOS.build_translate_label(int(label_id), self.view)
            self.view.replace(edit, region, new)


class SwitchXmlFolderCommand(QuickPanelCommand):

    """
    switch to same file in different XML folder if available
    """

    def is_visible(self):
        return bool(INFOS.addon) and len(INFOS.addon.xml_folders) > 1

    def run(self):
        view = self.window.active_view()
        self.nodes = []
        line, _ = view.rowcol(view.sel()[0].b)
        filename = os.path.basename(view.file_name())
        for folder in INFOS.addon.xml_folders:
            node = {"file": os.path.join(INFOS.addon.path, folder, filename),
                    "line": line + 1}
            self.nodes.append(node)
        self.window.show_quick_panel(items=INFOS.addon.xml_folders,
                                     on_select=self.on_done,
                                     selected_index=0,
                                     on_highlight=self.show_preview)

    def on_done(self, index):
        if index == -1:
            return None
        node = self.nodes[index]
        self.window.open_file("%s:%i" % (node["file"], node["line"]),
                              sublime.ENCODED_POSITION)
