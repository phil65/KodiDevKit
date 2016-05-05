# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
KodiDevKit is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""

import sublime
import sublime_plugin
import re
import webbrowser
from lxml import etree as ET
import platform
import os
import logging

from .libs import Utils
from .libs.kodijson import KodiJson

APP_NAME = "Kodi"
SETTINGS_FILE = 'kodidevkit.sublime-settings'

if sublime.platform() == "linux":
    KODI_PRESET_PATH = "/usr/share/%s/" % APP_NAME.lower()
elif sublime.platform() == "windows":
    KODI_PRESET_PATH = "C:/%s/" % APP_NAME.lower()
elif platform.system() == "Darwin":
    KODI_PRESET_PATH = os.path.join(os.path.expanduser("~"),
                                    "Applications",
                                    "%s.app" % APP_NAME,
                                    "Contents",
                                    "Resources",
                                    APP_NAME)
else:
    KODI_PRESET_PATH = ""

kodijson = KodiJson()


def plugin_loaded():
    kodijson.setup(sublime.load_settings(SETTINGS_FILE))


class OpenSourceFromLog(sublime_plugin.TextCommand):

    def run(self, edit):
        for region in self.view.sel():
            if region.empty():
                line_contents = self.view.substr(self.view.line(region))
                ma = re.search('File "(.*?)", line (\d*), in .*', line_contents)
                if ma:
                    sublime.active_window().open_file("%s:%s" % (ma.group(1), ma.group(2)),
                                                      sublime.ENCODED_POSITION)
                    return
                ma = re.search(r"', \('(.*?)', (\d+), (\d+), ", line_contents)
                if ma:
                    sublime.active_window().open_file("%s:%s:%s".format(ma.group(1),
                                                                        ma.group(2),
                                                                        ma.group(3)),
                                                      sublime.ENCODED_POSITION)
                    return
            else:
                self.view.insert(edit, region.begin(), self.view.substr(region))


class GoToOnlineHelpCommand(sublime_plugin.TextCommand):
    CONTROLS = {"group": "http://kodi.wiki/view/Group_Control",
                "grouplist": "http://kodi.wiki/view/Group_List_Control",
                "label": "http://kodi.wiki/view/Label_Control",
                "fadelabel": "http://kodi.wiki/view/Fade_Label_Control",
                "image": "http://kodi.wiki/view/Image_Control",
                "largeimage": "http://kodi.wiki/view/Large_Image_Control",
                "multiimage": "http://kodi.wiki/view/MultiImage_Control",
                "button": "http://kodi.wiki/view/Button_control",
                "radiobutton": "http://kodi.wiki/view/Radio_button_control",
                "selectbutton": "http://kodi.wiki/view/Group_Control",
                "togglebutton": "http://kodi.wiki/view/Toggle_button_control",
                "multiselect": "http://kodi.wiki/view/Multiselect_control",
                "spincontrol": "http://kodi.wiki/view/Spin_Control",
                "spincontrolex": "http://kodi.wiki/view/Settings_Spin_Control",
                "progress": "http://kodi.wiki/view/Progress_Control",
                "list": "http://kodi.wiki/view/List_Container",
                "wraplist": "http://kodi.wiki/view/Wrap_List_Container",
                "fixedlist": "http://kodi.wiki/view/Fixed_List_Container",
                "panel": "http://kodi.wiki/view/Text_Box",
                "rss": "http://kodi.wiki/view/RSS_feed_Control",
                "visualisation": "http://kodi.wiki/view/Visualisation_Control",
                "videowindow": "http://kodi.wiki/view/Video_Control",
                "edit": "http://kodi.wiki/view/Edit_Control",
                "epggrid": "http://kodi.wiki/view/EPGGrid_control",
                "mover": "http://kodi.wiki/view/Mover_Control",
                "resize": "http://kodi.wiki/view/Resize_Control"
                }

    def is_visible(self):
        region = self.view.sel()[0]
        line_contents = self.view.substr(self.view.line(region))
        scope_name = self.view.scope_name(region.b)
        return "text.xml" in scope_name and "<control " in line_contents

    def run(self, edit):
        region = self.view.sel()[0]
        line = self.view.line(region)
        line_contents = self.view.substr(line)
        try:
            root = ET.fromstring(line_contents + "</control>")
            control_type = root.attrib["type"]
            self.go_to_help(control_type)
        except:
            logging.debug("error when trying to open from %s" % line_contents)

    def go_to_help(self, word):
        """
        open browser and go to wiki page for control with type *word
        """
        webbrowser.open_new(self.CONTROLS[word])


class AppendTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, label):
        self.view.insert(edit, self.view.size(), label + "\n")


class LogCommand(sublime_plugin.TextCommand):

    def run(self, edit, label, panel_name='example'):
        if not hasattr(self, "output_view"):
            self.output_view = self.view.window().create_output_panel(panel_name)
        self.output_view.insert(edit, self.output_view.size(), label + '\n')
        self.output_view.show(self.output_view.size())
        self.view.window().run_command("show_panel", {"panel": "output." + panel_name})


class CreateElementRowCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel("Enter number of items to generate",
                                     "1",
                                     on_done=self.generate_items,
                                     on_change=None,
                                     on_cancel=None)

    def generate_items(self, num_items):
        self.window.run_command("replace_xml_elements", {"num_items": num_items})


class ReplaceXmlElementsCommand(sublime_plugin.TextCommand):

    def run(self, edit, num_items):
        if not num_items.isdigit():
            return None
        selected_text = self.view.substr(self.view.sel()[0])
        text = ""
        reg = re.search(r"\[(-?[0-9]+)\]", selected_text)
        offset = 0
        if reg:
            offset = int(reg.group(1))
        for i in range(int(num_items)):
            text = text + selected_text.replace("[%i]" % offset, str(i + offset)) + "\n"
            i += 1
        for region in self.view.sel():
            self.view.replace(edit, region, text)
            break


class EvaluateMathExpressionPromptCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel("Write Equation (x = selected int)",
                                     "x",
                                     self.evaluate,
                                     None,
                                     None)

    def evaluate(self, equation):
        self.window.run_command("evaluate_math_expression", {'equation': equation})


class EvaluateMathExpressionCommand(sublime_plugin.TextCommand):

    def run(self, edit, equation):
        for i, region in enumerate(self.view.sel()):
            text = self.view.substr(region)
            if text.replace('-', '').isdigit():
                new_text = eval(equation.replace("x", text).replace("i", str(i)))
                self.view.replace(edit, region, str(new_text).replace(".0", ""))


class ColorPickerCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        settings = sublime.load_settings('KodiColorPicker.sublime-settings')
        settings.set('color_pick_return', None)
        self.window.run_command('color_pick_api_is_available',
                                {'settings': 'KodiColorPicker.sublime-settings'})
        return bool(settings.get('color_pick_return', False))

    def run(self):
        settings = sublime.load_settings('KodiColorPicker.sublime-settings')
        settings.set('color_pick_return', None)
        self.window.run_command('color_pick_api_get_color',
                                {'settings': 'KodiColorPicker.sublime-settings', 'default_color': '#ff0000'})
        color = settings.get('color_pick_return')
        if color:
            self.window.active_view().run_command("insert",
                                                  {"characters": "FF" + color[1:]})


class SetKodiFolderCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel("Set Kodi folder",
                                     KODI_PRESET_PATH,
                                     self.set_kodi_folder,
                                     None,
                                     None)

    def set_kodi_folder(self, path):
        if os.path.exists(path):
            sublime.load_settings(SETTINGS_FILE).set("kodi_path", path)
            sublime.save_settings(SETTINGS_FILE)
        else:
            logging.critical("Folder %s does not exist." % path)


class ExecuteBuiltinPromptCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.settings = sublime.load_settings(SETTINGS_FILE)
        self.window.show_input_panel("Execute builtin",
                                     self.settings.get("prev_json_builtin", ""),
                                     self.execute_builtin,
                                     None,
                                     None)

    def execute_builtin(self, builtin):
        self.settings.set("prev_json_builtin", builtin)
        self.window.run_command("execute_builtin", {"builtin": builtin})


class ExecuteBuiltinCommand(sublime_plugin.WindowCommand):

    def run(self, builtin):
        params = {"addonid": "script.toolbox",
                  "params": {"info": "builtin",
                             "id": builtin}}
        kodijson.request_async(method="Addons.ExecuteAddon",
                               params=params)


class GetInfoLabelsPromptCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.settings = sublime.load_settings(SETTINGS_FILE)
        self.window.show_input_panel("Get InfoLabels (comma-separated)",
                                     self.settings.get("prev_infolabel", ""),
                                     self.show_info_label,
                                     None,
                                     None)

    @Utils.run_async
    def show_info_label(self, label_string):
        self.settings.set("prev_infolabel", label_string)
        words = label_string.split(",")
        self.window.run_command("log", {"label": "send request..."})
        result = kodijson.request(method="XBMC.GetInfoLabels",
                                  params={"labels": words})
        if result:
            self.window.run_command("log", {"label": "Got result:"})
            key, value = result["result"].popitem()
            self.window.run_command("log", {"label": str(value)})


class GetInfoBooleansPromptCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.settings = sublime.load_settings(SETTINGS_FILE)
        self.window.show_input_panel("Get boolean values (comma-separated)",
                                     self.settings.get("prev_boolean", ""),
                                     self.show_info_boolean,
                                     None,
                                     None)

    @Utils.run_async
    def show_info_boolean(self, label_string):
        self.settings.set("prev_boolean", label_string)
        words = label_string.split(",")
        self.window.run_command("log", {"label": "send request..."})
        result = kodijson.request(method="XBMC.GetInfoBooleans",
                                  params={"booleans": words})
        if result:
            self.window.run_command("log", {"label": "Got result:"})
            key, value = result["result"].popitem()
            self.window.run_command("log", {"label": str(value)})
