# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
KodiDevKit is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""

from urllib.request import Request, urlopen
import json
import base64

from . import Utils


class KodiJson(object):

    def __init__(self, *args, **kwargs):
        self.settings = kwargs.get("settings")

    def setup(self, settings):
        self.settings = settings

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
        except:
            return None
