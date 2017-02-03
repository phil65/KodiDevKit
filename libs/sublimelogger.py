# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
KodiDevKit is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""

import sublime
import logging


class SublimeLogHandler(logging.StreamHandler):

    def __init__(self):
        super().__init__()
        formatter = logging.Formatter('[KodiDevKit] %(asctime)s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        self.setFormatter(formatter)

    def emit(self, record):
        levels = {
            logging.CRITICAL: self.message,
            logging.ERROR: self.info,
            logging.WARNING: self.info,
            logging.INFO: self.debug,
            logging.DEBUG: self.debug,
            logging.NOTSET: self.debug,
        }
        # if settings.get("debug_mode"):
        log = levels[record.levelno]
        log(record)

    def flush(self):
        pass

    def debug(self, record):
        # if settings.get("debug_mode"):
        print(self.format(record))

    def info(self, record):
        wnd = sublime.active_window()
        wnd.run_command("log", {"label": self.format(record).strip()})

    @staticmethod
    def message(record):
        sublime.message_dialog(record.msg)


def config():
    logger = logging.getLogger()
    for hdlr in logger.handlers:  # remove all old handlers
        logger.removeHandler(hdlr)
    logger.addHandler(SublimeLogHandler())
    logger.setLevel(logging.INFO)
