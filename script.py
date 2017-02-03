import os
import sys
import codecs
from urllib.request import urlopen
import logging
from lxml import etree as ET

RESULTS_FILE = "results.txt"

settings = {"kodi_path": "C:/Kodi",
            "portable_mode": True,
            "language_folders": ["resource.language.en_gb", "English"]}

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format="")


def check_tags(check_type):
    """
    triggers of test of type "check_type", then formats and logs them
    """
    errors = INFOS.get_check_listitems(check_type)
    for e in errors:
        logging.info(e["message"])
        path = "/".join(e["file"].split(os.sep)[-2:])
        logging.info("%s: line %s\n" % (path, str(e["line"])))


def get_addons(reponames):
    """
    get available addons from the kodi addon repository
    """
    repo_list = 'http://mirrors.kodi.tv/addons/%s/addons.xml'
    addons = {}
    for reponame in reponames:
        logging.info("Downloading %s addon list" % reponame)
        req = urlopen(repo_list % reponame)
        data = req.read()
        req.close()
        root = ET.fromstring(data)
        for item in root.iter('addon'):
            addons[item.get('id')] = item.get('version')
    return addons


def check_dependencies(skinpath):
    """
    validate the addon dependencies
    """
    RELEASES = [{"version": '5.0.1',
                 "name": "gotham",
                 "allowed_addons": ['gotham']},
                {"version": '5.3.0',
                 "name": "helix",
                 "allowed_addons": ['gotham', 'helix']},
                {"version": '5.9.0',
                 "name": "isengard",
                 "allowed_addons": ['gotham', 'helix', 'isengard']},
                {"version": '5.10.0',
                 "name": "jarvis",
                 "allowed_addons": ['gotham', 'helix', 'isengard', 'jarvis']},
                {"version": '5.12.0',
                 "name": "krypton",
                 "allowed_addons": ['gotham', 'helix', 'isengard', 'jarvis', 'krypton']}]
    imports = {}
    str_releases = " / ".join([item["name"] for item in RELEASES])
    repo = input('Enter Kodi version (%s): ' % str_releases)
    root = utils.get_root_from_file(os.path.join(skinpath, 'addon.xml'))
    for item in root.iter('import'):
        imports[item.get('addon')] = item.get('version')
    for release in RELEASES:
        if repo == release["name"]:
            if imports['xbmc.gui'] > release["version"]:
                logging.info('xbmc.gui version incorrect')
            addons = get_addons(release["allowed_addons"])
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
    logger.addHandler(filehandler)
    if len(sys.argv) == 2:
        project_folder = sys.argv[1]
    else:
        project_folder = input("Enter Path to skin: ")
    INFOS.init_addon(project_folder)
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
    logging.info("\n\nADDON DEPENDENCY CHECK\n\n")
    check_dependencies(project_folder)
    logging.info("\n\nINCLUDE CHECK\n\n")
    check_tags("include")
    logging.info("\n\nVARIABLE CHECK\n\n")
    check_tags("variable")
    logging.info("\n\nFONT CHECK\n\n")
    check_tags("font")
    logging.info("\n\nLABEL CHECK\n\n")
    check_tags("label")
    logging.info("\n\nID CHECK\n\n")
    check_tags("id")
    logging.info("\n\nCHECK FOR COMMON MISTAKES\n\n")
    check_tags("general")
