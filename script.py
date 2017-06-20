# -*- coding: utf8 -*-

# Copyright (C) 2017 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import os
import sys
import codecs
import logging

RESULTS_FILE = "results.txt"

settings = {"kodi_path": "C:/Kodi",
            "portable_mode": True,
            "language_folders": ["resource.language.en_gb", "English"]}


def check_tags(check_type):
    """
    triggers of test of type "check_type", then formats and logs them
    """
    errors = INFOS.get_check_listitems(check_type)
    for e in errors:
        logging.info(e["message"])
        path = "/".join(e["file"].split(os.sep)[-2:])
        logging.info("%s: line %s\n" % (path, e["line"]))

print("test")
if __name__ == "__main__":
    from libs import utils
    from libs.infoprovider import InfoProvider
    from libs import chardet
    from libs.eol import eol
    INFOS = InfoProvider()
    open(RESULTS_FILE, 'w').close()
    INFOS.load_settings(settings)
    INFOS.load_data()
    filehandler = logging.FileHandler("result.txt", mode="w")
    formatter = logging.Formatter('%(asctime)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    filehandler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(filehandler)
    project_folder = sys.argv[1] if len(sys.argv) >= 2 else input("Enter Path to skin: ")
    INFOS.init_addon(project_folder)
    if len(sys.argv) < 3:
        repo = input('Enter Kodi version (%s): ' % " / ".join([item["name"] for item in INFOS.addon.RELEASES]))
    else:
        repo = sys.argv[2]
    INFOS.check_xml_files()
    for path in INFOS.addon.get_xml_files():
        if utils.check_bom(path):
            logging.info("found BOM. File: " + path)
        try:
            with codecs.open(path, "rb", encoding='utf-8', errors="strict") as f:
                text = f.read()
        except Exception:
            logging.info("Error when trying to read %s as UTF-8" % path)
            with codecs.open(path, "rb", errors="ignore") as f:
                rawdata = f.read()
            encoding = chardet.detect(rawdata)
            logging.info("detected encoding: %s" % encoding["encoding"])
            with codecs.open(path, "rb", encoding=encoding["encoding"]) as f:
                text = f.read()
    result = eol.eol_info_from_path_patterns([project_folder],
                                             recursive=True,
                                             includes=[],
                                             excludes=['.svn', '.git'])
    for item in result:
        if item[1] == '\n' or None:
            continue
        elif item[1] == '\r':
            logging.info("MAC Line Endings detected in " + item[0])
        else:
            logging.info("Windows Line Endings detected in " + item[0])
    logging.info("ADDON DEPENDENCY CHECK")
    INFOS.check_dependencies()
    logging.info("INCLUDE CHECK")
    check_tags("include")
    logging.info("VARIABLE CHECK")
    check_tags("variable")
    logging.info("FONT CHECK")
    check_tags("font")
    logging.info("LABEL CHECK")
    check_tags("label")
    logging.info("ID CHECK")
    check_tags("id")
    logging.info("CHECK FOR COMMON MISTAKES")
    check_tags("general")
