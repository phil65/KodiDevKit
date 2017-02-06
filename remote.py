# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
KodiDevKit is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""
import os
import sublime
import sublime_plugin
from .libs.adbdevice import AdbDevice

REMOTE = AdbDevice()
SETTINGS_FILE = 'kodidevkit.sublime-settings'


def plugin_loaded():
    """
    gets called when plugin is ready
    """
    REMOTE.setup(sublime.load_settings(SETTINGS_FILE))


class RemoteActionsCommand(sublime_plugin.WindowCommand):
    """
    Menu with all options related to ADB
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = None

    def run(self):
        """
        Show quick panel with all possible actions
        """
        self.settings = sublime.load_settings(SETTINGS_FILE)
        active_device = "Set device: %s" % self.settings.get("remote_ip", "")
        listitems = [active_device, "Reconnect", "Send this add-on",
                     "Get log", "Get Screenshot", "Clear cache", "Reboot"]
        self.window.show_quick_panel(items=listitems,
                                     on_select=self.on_done,
                                     selected_index=0)

    def on_done(self, index):
        """
        callback for menu items, gets called with *index of selected items
        """
        if index == -1:
            return None
        elif index == 0:
            self.window.show_input_panel("Set remote IP",
                                         self.settings.get("remote_ip", "192.168.0.1"),
                                         self.set_ip,
                                         None,
                                         None)
        elif index == 1:
            REMOTE.adb_reconnect_async()
            self.window.run_command("remote_actions")
        elif index == 2:
            variables = self.window.active_view().extract_variables()
            if "folder" in variables:
                REMOTE.push_to_box(variables["folder"])
        elif index == 3:
            plugin_path = os.path.join(sublime.packages_path(), "KodiDevKit")
            REMOTE.get_log(self.open_file, plugin_path)
        elif index == 4:
            plugin_path = os.path.join(sublime.packages_path(), "KodiDevKit")
            REMOTE.get_screenshot(self.open_file, plugin_path)
        elif index == 5:
            REMOTE.clear_cache()
        elif index == 6:
            REMOTE.reboot()

    def open_file(self, path):
        """
        used as callback, opens file with *path
        """
        self.window.open_file(path)

    def set_ip(self, ip):
        """
        set and save ip of adb device, return to actions menu when finished
        """
        self.settings.set("remote_ip", ip)
        sublime.save_settings(SETTINGS_FILE)
        self.window.run_command("remote_actions")
