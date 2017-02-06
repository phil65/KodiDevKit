# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
KodiDevKit is a tool to assist with Kodi skinning / scripting using Sublime Text 3
"""

from . import utils


class Window(object):

    def __init__(self, path, *args):
        self.root = utils.get_root_from_file(path)

    def get_controls(self, control_type):
        for node in self.root.xpath(".//control[@type='%s']" % control_type):
            yield node

    def xpath(self, *args, **kwargs):
        return self.root.xpath(*args, **kwargs)
