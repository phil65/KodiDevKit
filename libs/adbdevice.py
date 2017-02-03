# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
KodiDevKit is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""

import subprocess
from . import Utils
import os
import logging


class AdbDevice(object):

    """
    Class to communicate with Android Devices via ADB.
    """

    def __init__(self):
        self.is_busy = False

    def setup(self, settings):
        self.settings = settings
        self.connected = False
        self.userdata_folder = self.settings.get("remote_userdata_folder")
        self.ip = self.settings.get("remote_ip")

    @staticmethod
    def cmd(program, args):
        command = [program]
        for arg in args:
            command.append(arg)
        logging.warning(" ".join(command))
        try:
            output = subprocess.check_output(command,
                                             shell=True,
                                             stderr=subprocess.STDOUT)
            logging.warning(output.decode("utf-8").replace('\r', '').replace('\n', ''))
        except subprocess.CalledProcessError as e:
            logging.warning("%s\nErrorCode: %s" % (e, str(e.returncode)))
        except Exception as e:
            logging.warning(e)
        # proc = subprocess.Popen(['echo', '"to stdout"'],
        #                     stdout=subprocess.PIPE)
        # stdout_value = proc.communicate()[0]

    # @Utils.check_busy
    def adb_connect(self, ip):
        self.ip = ip
        logging.warning("Connect to remote with ip %s" % ip)
        self.cmd("adb", ["connect", ip])
        self.connected = True

    @Utils.run_async
    @Utils.check_busy
    def adb_connect_async(self, ip):
        self.adb_connect(ip)

    @Utils.check_busy
    def adb_reconnect(self, ip=""):
        if not ip:
            ip = self.ip
        self.adb_disconnect()
        self.adb_connect(ip)

    @Utils.run_async
    def adb_reconnect_async(self, ip=""):
        self.adb_reconnect(ip)

    # @Utils.check_busy
    def adb_disconnect(self):
        logging.warning("Disconnect from remote")
        self.cmd("adb", ["disconnect"])
        self.connected = False

    @Utils.run_async
    @Utils.check_busy
    def adb_disconnect_async(self):
        self.adb_disconnect()

    @Utils.check_busy
    def adb_push(self, source, target):
        if not target.endswith('/'):
            target += '/'
        self.cmd("adb", ["push", source.replace('\\', '/'), target.replace('\\', '/')])

    @Utils.run_async
    @Utils.check_busy
    def adb_push_async(self, source, target):
        self.adb_push(source, target)

    @Utils.check_busy
    def adb_pull(self, path, target):
        self.cmd("adb", ["pull", path, target])

    @Utils.run_async
    @Utils.check_busy
    def adb_pull_async(self, path, target):
        self.adb_pull(path, target)

    @Utils.run_async
    @Utils.check_busy
    def adb_restart_server(self):
        pass

    @Utils.run_async
    @Utils.check_busy
    def push_to_box(self, addon, all_file=False):
        logging.warning("push %s to remote" % addon)
        for root, _, files in os.walk(addon):
            # ignore git files
            if ".git" in root.split(os.sep):
                continue
            if not all_file and os.path.basename(root) not in ['1080i', '720p']:
                continue
            target = '{}/addons/{}{}'.format(self.userdata_folder,
                                             os.path.basename(addon),
                                             root.replace(addon, "").replace('\\', '/'))
            self.cmd("adb", ["shell", "mkdir", target])
            for f in files:
                if f.endswith(('.pyc', '.pyo')):
                    continue
                self.cmd("adb", ["push",
                                 os.path.join(root, f).replace('\\', '/'),
                                 target.replace('\\', '/')])
        logging.warning("All files pushed")

    @Utils.run_async
    def get_log(self, open_function, target):
        logging.warning("Pull logs from remote")
        self.adb_pull("%s/temp/xbmc.log" % self.userdata_folder, target)
        # self.adb_pull("%stemp/xbmc.old.log" % self.userdata_folder)
        logging.warning("Finished pulling logs")
        open_function(os.path.join(target, "xbmc.log"))

    @Utils.run_async
    @Utils.check_busy
    def get_screenshot(self, f_open, target):
        logging.warning("Pull screenshot from remote")
        self.cmd("adb", ["shell", "screencap", "-p", "/sdcard/screen.png"])
        self.cmd("adb", ["pull", "/sdcard/screen.png", target])
        self.cmd("adb", ["shell", "rm", "/sdcard/screen.png"])
        # self.adb_pull("%stemp/xbmc.old.log" % self.userdata_folder)
        logging.warning("Finished pulling screenshot")
        f_open(os.path.join(target, "screen.png"))

    @Utils.run_async
    @Utils.check_busy
    def clear_cache(self):
        self.cmd("adb", ["shell", "rm", "-rf", os.path.join(self.userdata_folder, "temp")])

    @Utils.run_async
    def reboot(self):
        self.cmd("adb", ["reboot"])
