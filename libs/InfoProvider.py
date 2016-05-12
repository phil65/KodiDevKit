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

from . import Utils
from .addon import Addon
from .kodi import kodi
from .ImageParser import get_image_size


# c&p from wiki
WINDOW_MAP = [("home", "WINDOW_HOME", " 10000", "0", "Home.xml"),
              ("programs", "WINDOW_PROGRAMS", " 10001", "1", "MyPrograms.xml"),
              ("pictures", "WINDOW_PICTURES", " 10002", "2", "MyPics.xml"),
              ("filemanager", "WINDOW_FILES", "10003", "3", "FileManager.xml"),
              ("settings", "WINDOW_SETTINGS_MENU", "10004", "4", "Settings.xml"),
              ("systeminfo", "WINDOW_SYSTEM_INFORMATION", "10007", "7", "SettingsSystemInfo.xml"),
              ("screencalibration", "WINDOW_MOVIE_CALIBRATION", "10011", "11", "SettingsScreenCalibration.xml"),
              ("picturessettings", "WINDOW_SETTINGS_MYPICTURES", "10012", "12", "SettingsCategory.xml"),
              ("programssettings", "WINDOW_SETTINGS_MYPROGRAMS", "10013", "13", "SettingsCategory.xml"),
              ("musicsettings", "WINDOW_SETTINGS_MYMUSIC", " 10015", "15", "SettingsCategory.xml"),
              ("systemsettings", "WINDOW_SETTINGS_SYSTEM", "10016", "16", "SettingsCategory.xml"),
              ("videossettings", "WINDOW_SETTINGS_MYVIDEOS", "10017", "17", "SettingsCategory.xml"),
              ("servicesettings", "WINDOW_SETTINGS_SERVICE", " 10018", "18", "SettingsCategory.xml"),
              ("appearancesettings", "WINDOW_SETTINGS_APPEARANCE", "10019", "19", "SettingsCategory.xml"),
              ("interfacesettings", "WINDOW_SETTINGS_APPEARANCE", "10019", "19", "SettingsCategory.xml"),
              ("pvrsettings", "WINDOW_SETTINGS_MYPVR", "10021", "21", "SettingsCategory.xml"),
              ("videos", "WINDOW_VIDEO_NAV", "10025", "25", "MyVideoNav.xml"),
              ("videoplaylist", "WINDOW_VIDEO_PLAYLIST", "10028", "28", "MyVideoPlaylist.xml"),
              ("loginscreen", "WINDOW_LOGINSCREEN", "10029", "29", "LoginScreen.xml"),
              ("profiles", "WINDOW_SETTINGS_PROFILES", "10034", "34", "SettingsProfile.xml"),
              ("addonbrowser", "WINDOW_ADDON_BROWSER", "10040", "40", "AddonBrowser.xml"),
              ("yesnodialog", "WINDOW_DIALOG_YES_NO", "10100", "100", "DialogConfirm.xml"),
              ("progressdialog", "WINDOW_DIALOG_PROGRESS", "10101", "101", "DialogConfirm.xml"),
              ("virtualkeyboard", "WINDOW_DIALOG_KEYBOARD", "10103", "103", "DialogKeyboard.xml"),
              ("volumebar", "WINDOW_DIALOG_VOLUME_BAR", "10104", "104", "DialogVolumeBar.xml"),
              ("contextmenu", "WINDOW_DIALOG_CONTEXT_MENU", "10106", "106", "DialogContextMenu.xml"),
              # ("infodialog", "WINDOW_DIALOG_KAI_TOAST", "10107", "107", "DialogKaiToast.xml"),
              ("notification", "WINDOW_DIALOG_KAI_TOAST", "10107", "107", "DialogNotification.xml"),
              ("numericinput", "WINDOW_DIALOG_NUMERIC", "10109", "109", "DialogNumeric.xml"),
              ("shutdownmenu", "WINDOW_DIALOG_BUTTON_MENU", "10111", "111", "DialogButtonMenu.xml"),
              ("mutebug", "WINDOW_DIALOG_MUTE_BUG", "10113", "113", "DialogMuteBug.xml"),
              ("playercontrols", "WINDOW_DIALOG_PLAYER_CONTROLS", "10114", "114", "PlayerControls.xml"),
              ("seekbar", "WINDOW_DIALOG_SEEK_BAR", "10115", "115", "DialogSeekBar.xml"),
              ("musicosd", "WINDOW_DIALOG_MUSIC_OSD", "10120", "120", "MusicOSD.xml"),
              ("visualisationpresetlist", "WINDOW_DIALOG_VIS_PRESET_LIST", "10122", "122", "DialogSelect.xml"),
              ("osdvideosettings", "WINDOW_DIALOG_VIDEO_OSD_SETTINGS", "10123", "123", "VideoOSDSettings.xml"),
              ("osdaudiosettings", "WINDOW_DIALOG_AUDIO_OSD_SETTINGS", "10124", "124", "VideoOSDSettings.xml"),
              ("videobookmarks", "WINDOW_DIALOG_VIDEO_BOOKMARKS", "10125", "125", "VideoOSDBookmarks.xml"),
              ("filebrowser", "WINDOW_DIALOG_FILE_BROWSER", "10126", "126", "FileBrowser.xml"),
              ("networksetup", "WINDOW_DIALOG_NETWORK_SETUP", "10128", "128", "DialogSettings.xml"),
              ("mediasource", "WINDOW_DIALOG_MEDIA_SOURCE", "10129", "129", "DialogMediaSource.xml"),
              ("profilesettings", "WINDOW_PROFILE_SETTINGS", "10130", "130", "ProfileSettings.xml"),
              ("locksettings", "WINDOW_LOCK_SETTINGS", "10131", "131", "LockSettings.xml"),
              ("contentsettings", "WINDOW_DIALOG_CONTENT_SETTINGS", "10132", "132", "DialogSettings.xml"),
              ("favourites", "WINDOW_DIALOG_FAVOURITES", "10134", "134", "DialogFavourites.xml"),
              ("songinformation", "WINDOW_DIALOG_SONG_INFO", "10135", "135", "DialogMusicInfo.xml"),
              ("smartplaylisteditor", "WINDOW_DIALOG_SMART_PLAYLIST_EDITOR", "10136", "136", "SmartPlaylistEditor.xml"),
              ("smartplaylistrule", "WINDOW_DIALOG_SMART_PLAYLIST_RULE", "10137", "137", "SmartPlaylistRule.xml"),
              ("busydialog", "WINDOW_DIALOG_BUSY", "10138", "138", "DialogBusy.xml"),
              ("pictureinfo", "WINDOW_DIALOG_PICTURE_INFO", "10139", "139", "DialogPictureInfo.xml"),
              ("addonsettings", "WINDOW_DIALOG_ADDON_SETTINGS", "10140", "140", "DialogAddonSettings.xml"),
              ("fullscreeninfo", "WINDOW_DIALOG_FULLSCREEN_INFO", "10142", "142", "DialogFullScreenInfo.xml"),
              ("sliderdialog", "WINDOW_DIALOG_SLIDER", "10145", "145", "DialogSlider.xml"),
              ("addoninformation", "WINDOW_DIALOG_ADDON_INFO", "10146", "146", "DialogAddonInfo.xml"),
              ("textviewer", "WINDOW_DIALOG_TEXT_VIEWER", "10147", "147", "DialogTextViewer.xml"),
              ("peripherals", "WINDOW_DIALOG_PERIPHERAL_MANAGER", "10149", "149", "DialogSelect.xml"),
              ("peripheralsettings", "WINDOW_DIALOG_PERIPHERAL_SETTINGS", "10150", "150", "DialogSettings.xml"),
              ("extendedprogressdialog", "WINDOW_DIALOG_EXT_PROGRESS", "10151", "151", "DialogExtendedProgressBar.xml"),
              ("mediafilter", "WINDOW_DIALOG_MEDIA_FILTER", "10152", "152", "DialogMediaFilter.xml"),
              ("subtitlesearch", "WINDOW_DIALOG_SUBTITLES", "10153", "153", "DialogSubtitles.xml"),
              ("musicplaylist", "WINDOW_MUSIC_PLAYLIST", "10500", "500", "MyMusicPlaylist.xml"),
              ("musicfiles", "WINDOW_MUSIC_FILES", "10501", "501", "MyMusicSongs.xml"),
              ("musiclibrary", "WINDOW_MUSIC_NAV", "10502", "502", "MyMusicNav.xml"),
              ("musicplaylisteditor", "WINDOW_MUSIC_PLAYLIST_EDITOR", "10503", "503", "MyMusicPlaylistEditor.xml"),
              ("tvchannels", "WINDOW_TV_CHANNELS", "10615", "615", "MyPVRChannels.xml"),
              ("tvrecordings", "WINDOW_TV_RECORDINGS", "10616", "616", "MyPVRRecordings.xml"),
              ("tvguide", "WINDOW_TV_GUIDE", "10617", "617", "MyPVRGuide.xml"),
              ("tvtimers", "WINDOW_TV_TIMERS", "10618", "618", "MyPVRTimers.xml"),
              ("tvsearch", "WINDOW_TV_SEARCH", "10619", "619", "MyPVRSearch.xml"),
              ("radiochannels", "WINDOW_RADIO_CHANNELS", "10620", "620", "MyPVRChannels.xml"),
              ("radiorecordings", "WINDOW_RADIO_RECORDINGS", "10621", "621", "MyPVRRecordings.xml"),
              ("radioguide", "WINDOW_RADIO_GUIDE", "10622", "622", "MyPVRGuide.xml"),
              ("radiotimers", "WINDOW_RADIO_TIMERS", "10623", "623", "MyPVRTimers.xml"),
              ("radiosearch", "WINDOW_RADIO_SEARCH", "10624", "624", "MyPVRSearch.xml"),
              ("pvrguideinfo", "WINDOW_DIALOG_PVR_GUIDE_INFO", "10602", "602", "DialogPVRGuideInfo.xml"),
              ("pvrrecordinginfo", "WINDOW_DIALOG_PVR_RECORDING_INFO", "10603", "603", "DialogPVRRecordingInfo.xml"),
              ("pvrtimersetting", "WINDOW_DIALOG_PVR_TIMER_SETTING", "10604", "604", "DialogPVRTimerSettings.xml"),
              ("pvrgroupmanager", "WINDOW_DIALOG_PVR_GROUP_MANAGER", "10605", "605", "DialogPVRGroupManager.xml"),
              ("pvrchannelmanager", "WINDOW_DIALOG_PVR_CHANNEL_MANAGER", "10606", "606", "DialogPVRChannelManager.xml"),
              ("pvrguidesearch", "WINDOW_DIALOG_PVR_GUIDE_SEARCH", "10607", "607", "DialogPVRGuideSearch.xml"),
              ("pvrosdchannels", "WINDOW_DIALOG_PVR_OSD_CHANNELS", "10610", "610", "DialogPVRChannelsOSD.xml"),
              ("pvrosdguide", "WINDOW_DIALOG_PVR_OSD_GUIDE", "10611", "611", "DialogPVRGuideOSD.xml"),
              ("selectdialog", "WINDOW_DIALOG_SELECT", "12000", "2000", "DialogSelect.xml"),
              ("musicinformation", "WINDOW_MUSIC_INFO", "12001", "2001", "DialogAlbumInfo.xml"),
              ("okdialog", "WINDOW_DIALOG_OK", "12002", "2002", "DialogConfirm.xml"),
              ("movieinformation", "WINDOW_VIDEO_INFO", "12003", "2003", "DialogVideoInfo.xml"),
              ("fullscreenvideo", "WINDOW_FULLSCREEN_VIDEO", "12005", "2005", "VideoFullScreen.xml"),
              ("visualisation", "WINDOW_VISUALISATION", "12006", "2006", "MusicVisualisation.xml"),
              ("slideshow", "WINDOW_SLIDESHOW", "12007", "2007", "SlideShow.xml"),
              ("filestackingdialog", "WINDOW_DIALOG_FILESTACKING", "12008", "2008", "DialogFileStacking.xml"),
              ("weather", "WINDOW_WEATHER", "12600", "2600", "MyWeather.xml"),
              ("videoosd", "WINDOW_OSD", "12901", "2901", "VideoOSD.xml"),
              ("startup", "WINDOW_STARTUP_ANIM", "12999", "2999", "Startup.xml"),
              ("skinsettings", "WINDOW_SKIN_SETTINGS", "10035", "35", "SkinSettings.xml"),
              ("pointer", "-", "-", "105", "Pointer.xml"),
              ("musicoverlay", "WINDOW_MUSIC_OVERLAY", "12903", "2903", "MusicOverlay.xml"),
              ("videooverlay", "WINDOW_VIDEO_OVERLAY", "12904", "2904", "VideoOverlay.xml")]
WINDOW_FILENAMES = [item[4] for item in WINDOW_MAP]
WINDOW_NAMES = [item[0] for item in WINDOW_MAP]
WINDOW_IDS = [item[3] for item in WINDOW_MAP]

COMMON = ["description", "camera", "depth", "posx", "posy", "top", "bottom", "left", "right", "centertop", "centerbottom", "centerleft", "centerright", "width", "height", "visible", "include", "animation"]
# tags allowed for containers
LIST_COMMON = ["defaultcontrol", "focusedlayout", "itemlayout", "offsetx", "offsety", "content", "onup", "ondown", "onleft", "onright", "oninfo", "onback", "onclick", "onfocus", "onunfocus", "orientation", "preloaditems", "scrolltime", "pagecontrol", "viewtype", "autoscroll", "hitrect"]
LABEL_COMMON = ["font", "textcolor", "align", "aligny", "label"]
# allowed child nodes for different control types (+ some other nodes)
TAG_CHECKS = [[".//*[@type='button']/*", COMMON + LABEL_COMMON + ["colordiffuse", "texturefocus", "texturenofocus", "label2", "wrapmultiline", "disabledcolor", "selectedcolor", "shadowcolor", "textoffsetx",
                                                                  "textoffsety", "pulseonselect", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "textwidth",
                                                                  "focusedcolor", "angle", "hitrect", "enable"]],
              [".//*[@type='radiobutton']/*", COMMON + LABEL_COMMON + ["colordiffuse", "texturefocus", "texturenofocus", "selected", "disabledcolor", "selectedcolor", "shadowcolor", "textoffsetx",
                                                                       "textoffsety", "pulseonselect", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "textwidth",
                                                                       "focusedcolor", "angle", "hitrect", "enable", "textureradioonfocus", "textureradioofffocus", "textureradioondisabled", "textureradiooffdisabled", "textureradioonnofocus",
                                                                       "textureradiooffnofocus", "textureradioon", "textureradiooff", "radioposx", "radioposy", "radiowidth", "radioheight"]],
              [".//*[@type='spincontrol']/*", COMMON + LABEL_COMMON + ["colordiffuse", "textureup", "textureupfocus", "textureupdisabled", "texturedown", "texturedownfocus", "texturedowndisabled", "spinwidth", "spinheight", "spinposx", "spinposy",
                                                                       "subtype", "disabledcolor", "focusedcolor", "shadowcolor", "textoffsetx", "textoffsety", "pulseonselect", "onfocus", "onunfocus", "onup", "onleft",
                                                                       "onright", "ondown", "onback", "hitrect", "enable", "showonepage", "reverse"]],
              [".//*[@type='togglebutton']/*", COMMON + LABEL_COMMON + ["colordiffuse", "texturefocus", "alttexturefocus", "alttexturenofocus", "altclick", "texturenofocus", "altlabel", "usealttexture",
                                                                        "disabledcolor", "shadowcolor", "textoffsetx", "textoffsety", "pulseonselect", "onclick", "onfocus", "onunfocus", "onup", "onleft",
                                                                        "onright", "ondown", "onback", "textwidth", "focusedcolor", "subtype", "hitrect", "enable"]],
              [".//*[@type='label']/*", COMMON + LABEL_COMMON + ["scroll", "scrollout", "info", "number", "angle", "haspath", "selectedcolor", "shadowcolor", "disabledcolor", "pauseatend", "wrapmultiline",
                                                                 "scrollspeed", "scrollsuffix", "textoffsetx", "textoffsety"]],
              [".//*[@type='textbox']/*", COMMON + LABEL_COMMON + ["autoscroll", "info", "selectedcolor", "shadowcolor", "pagecontrol"]],
              [".//*[@type='edit']/*", COMMON + LABEL_COMMON + ["colordiffuse", "hinttext", "textoffsetx", "textoffsety", "pulseonselect", "disabledcolor", "invalidcolor", "focusedcolor", "shadowcolor",
                                                                "texturefocus", "texturenofocus", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "textwidth", "hitrect", "enable"]],
              [".//*[@type='image']/*", COMMON + ["align", "aligny", "aspectratio", "fadetime", "colordiffuse", "texture", "bordertexture", "bordersize", "info"]],
              [".//*[@type='multiimage']/*", COMMON + ["align", "aligny", "aspectratio", "fadetime", "colordiffuse", "imagepath", "timeperimage", "loop", "info", "randomize", "pauseatend"]],
              [".//*[@type='scrollbar']/*", COMMON + ["texturesliderbackground", "texturesliderbar", "texturesliderbarfocus", "textureslidernib", "textureslidernibfocus", "pulseonselect", "orientation",
                                                      "showonepage", "pagecontrol", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback"]],
              [".//*[@type='progress']/*", COMMON + ["texturebg", "lefttexture", "colordiffuse", "righttexture", "overlaytexture", "midtexture", "info", "reveal"]],
              [".//*[@type='grouplist']/*", COMMON + ["control", "align", "itemgap", "orientation", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "scrolltime", "usecontrolcoords", "defaultcontrol", "pagecontrol"]],
              [".//*[@type='videowindow']/*", COMMON],
              [".//*[@type='visualisation']/*", COMMON],
              [".//*[@type='list']/*", COMMON + LIST_COMMON],
              [".//*[@type='wraplist']/*", COMMON + LIST_COMMON + ["focusposition"]],
              [".//*[@type='panel']/*", COMMON + LIST_COMMON],
              [".//*[@type='fixedlist']/*", COMMON + LIST_COMMON + ["movement", "focusposition"]],
              [".//content/*", ["item", "include"]],
              [".//itemlayout/* | .//focusedlayout/*", ["control", "include"]],
              ["/includes/*", ["include", "default", "constant", "variable", "expression"]],
              ["/window/*", ["include", "defaultcontrol", "depth", "menucontrol", "onload", "onunload", "controls", "allowoverlay", "views", "coordinates", "animation", "visible", "zorder", "fontset", "backgroundcolor"]],
              ["/fonts/*", ["fontset"]],
              [".//variable/*", ["value"]]]
# allowed attributes for some specific nodes
ATT_CHECKS = [[["aspectratio"], ["description", "align", "aligny", "scalediffuse"]],
              [["texture"], ["description", "background", "flipx", "flipy", "fallback", "border", "diffuse", "colordiffuse"]],
              [["label"], ["description", "fallback"]],
              [["autoscroll"], ["time", "reverse", "delay", "repeat"]],
              [["defaultcontrol"], ["description", "always"]],
              [["visible"], ["description", "allowhiddenfocus"]],
              [["align", "aligny", "posx", "posy", "textoffsetx", "textoffsety"], ["description"]],
              [["height", "width"], ["description", "min", "max"]],
              [["camera"], ["description", "x", "y"]],
              [["hitrect"], ["description", "x", "y", "w", "h"]],
              [["onload", "onunload", "onclick", "onleft", "onright", "onup", "ondown", "onback", "onfocus", "onunfocus", "value"], ["description", "condition"]],
              [["property"], ["description", "name", "fallback"]],
              [["focusedlayout", "itemlayout"], ["description", "height", "width", "condition"]],
              [["item"], ["description", "id"]],
              [["control"], ["description", "id", "type"]],
              [["variable"], ["description", "name"]],
              [["expression"], ["description", "name"]],
              [["constant"], ["description", "name"]],
              [["include"], ["description", "name", "condition", "file", "content"]],
              [["animation"], ["description", "start", "end", "effect", "tween", "easing", "time", "condition", "reversible", "type", "center", "delay", "pulse", "loop", "acceleration"]],
              [["effect"], ["description", "start", "end", "tween", "easing", "time", "condition", "type", "center", "delay", "pulse", "loop", "acceleration"]]]
# all_tags = [d[0] for d in att_checks]
# check correct parantheses for some nodes
BRACKET_TAGS = ["visible", "enable", "usealttexture", "selected", "expression"]
# check some nodes to use noop instead of "-" / empty
NOOP_TAGS = ["onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback"]
# check that some nodes only exist once on each level
# TODO: special cases: label for fadelabel
DOUBLE_TAGS = ["camera", "posx", "posy", "top", "bottom", "left", "right", "centertop", "centerbottom", "centerleft", "centerright", "width", "height",
               "colordiffuse", "texturefocus", "texturenofocus", "font", "selected", "textcolor", "disabledcolor", "selectedcolor",
               "shadowcolor", "align", "aligny", "textoffsetx", "textoffsety", "pulseonselect", "textwidth", "focusedcolor", "invalidcolor", "angle", "hitrect"]
# check that some nodes only contain specific text
ALLOWED_TEXT = [[["align"], ["left", "center", "right", "justify"]],
                [["aspectratio"], ["keep", "scale", "stretch", "center"]],
                [["aligny"], ["top", "center", "bottom"]],
                [["orientation"], ["horizontal", "vertical"]],
                [["subtype"], ["page", "int", "float", "text"]],
                [["action"], ["volume", "seek"]],
                [["scroll", "randomize", "scrollout", "pulseonselect", "reverse", "usecontrolcoords"], ["false", "true", "yes", "no"]]]
# check that some attributes may only contain specific values
ALLOWED_ATTR = [["align", ["left", "center", "right", "justify"]],
                ["aligny", ["top", "center", "bottom"]],
                ["flipx", ["true", "false"]],
                ["flipy", ["true", "false"]]]


PARSER = ET.XMLParser(remove_blank_text=True, remove_comments=True)


class InfoProvider(object):

    def __init__(self):
        self.addon = None

    def load_data(self):
        """
        loads the xml with control nodes for sanity checking (controls.xml)
        as well as builtins including their help string (data.xml)
        """
        # TODO: clean this up
        try:
            # since we get packaged we need to use load_resource() to load external files
            import sublime
            text = sublime.load_resource("Packages/KodiDevKit/data/controls.xml").encode("utf-8")
            self.template_root = ET.fromstring(text, PARSER)
            # resolve includes
            text = sublime.load_resource("Packages/KodiDevKit/data/data.xml").encode("utf-8")
            root = ET.fromstring(text, PARSER)
        except Exception:
            # fallback to old method so that class still can get used without sublime import
            path = os.path.normpath(os.path.abspath(__file__))
            folder = os.path.split(path)[0]
            self.template_root = Utils.get_root_from_file(os.path.join(folder, "..", "data", "controls.xml"))
            root = Utils.get_root_from_file(os.path.join(folder, "..", "data", "data.xml"))
        self.builtins = []
        self.conditions = []
        for item in root.find("builtins"):
            self.builtins.append([item.find("code").text, item.find("help").text])
        for item in root.find("conditions"):
            self.conditions.append([item.find("code").text, item.find("help").text])
        # TODO: resolve includes

        # for node in self.template.iterchildren():
        #     logging.info(node.tag)

    def init_addon(self, path):
        """
        scan addon folder and parse skin content etc
        """
        self.addon = None
        addon_xml = Utils.check_paths([os.path.join(path, "addon.xml")])
        if addon_xml:
            self.addon = Addon.by_project(path, self.settings)
            logging.info("Kodi project detected: " + path)
            # sublime.status_message("KodiDevKit: successfully loaded addon")

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
            for item in WINDOW_FILENAMES:
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
            for node in self.addon.colors:
                if node["name"] == keyword and node["file"].endswith("defaults.xml"):
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
            folder = po_file.fpath.split(os.sep)[-2]
            if folder == "resources":
                folder = po_file.fpath.split(os.sep)[-3].replace("resource.language.", "")
            if hit.msgstr:
                tooltips += "<b>%s:</b> %s<br>" % (folder, hit.msgstr)
            else:
                tooltips += "<b>%s:</b> %s<br>" % (folder, hit.msgid)
        return tooltips

    def get_po_files(self):
        """
        get addon po files and update po files list
        """
        return kodi.po_files + self.addon.po_files

    def get_ancestor_info(self, path, line):
        """
        iter through ancestors and return info about absolute position
        """
        element = None
        root = Utils.get_root_from_file(path)
        tree = ET.ElementTree(root)
        for e in tree.iter():
            if line <= e.sourceline:
                element = e
                break
        values = {}
        for anc in element.iterancestors():
            for sib in anc.iterchildren():
                if sib.tag in ["posx", "posy"]:
                    if sib.tag in values:
                        values[sib.tag].append(sib.text)
                    else:
                        values[sib.tag] = [sib.text]
        if not values:
            return ""
        anc_info = ["<b>{}:</b> {}".format(k, v) for k, v in values.items()]
        anc_info = "<br>".join(anc_info)
        return "<b>Absolute position</b><br>{}".format(anc_info)

    def get_font_info(self, font_name, folder):
        """
        return formatted string containing font info
        """
        node = self.addon.return_node(font_name, folder=folder)
        if not node:
            return ""
        root = ET.fromstring(node["content"])
        return ["<b>%s:</b> %s<br>" % (e.tag, e.text) for e in root.iterchildren()]

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
                root = Utils.get_root_from_file(path)
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
        imagepath = self.addon.translate_path(path)
        if not os.path.exists(imagepath) or os.path.isdir(imagepath):
            return ""
        width, height = get_image_size(imagepath)
        file_size = os.path.getsize(imagepath) / 1024
        return "<b>Dimensions:</b> %sx%s <br><b>File size:</b> %.2f kb" % (width, height, file_size)

    def check_fonts(self):
        listitems = []
        font_refs = self.addon.get_font_refs()
        # get estuary fonts..
        estuary_fonts = []
        estuary_font_file = os.path.join(self.kodi_path, "addons", "skin.estuary", "1080i", "Font.xml")
        root = Utils.get_root_from_file(estuary_font_file)
        if root is not None:
            for node in root.find("fontset").findall("font"):
                estuary_fonts.append(node.find("name").text)
            # check fonts from each folder independently....
        for folder in self.addon.xml_folders:
            fontlist = ["-"]
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
                root = Utils.get_root_from_file(path)
                if root is None:
                    continue
                if "id" in root.attrib:
                    window_ids.append(root.attrib["id"])
                # get all nodes with ids....
                xpath = ".//*[@id]"
                for node in root.xpath(xpath):
                    item = {"name": node.attrib["id"],
                            "type": node.tag,
                            "file": path,
                            "line": node.sourceline}
                    defines.append(item)
                # get all conditions....
                xpath = ".//*[@condition]"
                for node in root.xpath(xpath):
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
                xpath = ".//" + " | .//".join(bracket_tags)
                for node in root.xpath(xpath):
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
                elif item["name"] in WINDOW_IDS:
                    windowname = WINDOW_NAMES[WINDOW_IDS.index(item["name"])]
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

    def resolve_include(self, ref, folder):
        if not ref.text:
            return None
        include_names = [item["name"] for item in self.addon.includes[folder]]
        if ref.text not in include_names:
            return None
        index = include_names.index(ref.text)
        node = self.addon.includes[folder][index]
        root = ET.fromstring(node["content"])
        return self.resolve_includes(root, folder)

    def resolve_includes(self, xml_source, folder):
        for node in xml_source.xpath(".//include"):
            if node.text:
                new_include = self.resolve_include(node, folder)
                if new_include is not None:
                    node.getparent().replace(node, new_include)
        return xml_source

    def check_labels(self):
        listitems = []
        refs = []
        regexs = [r"\$LOCALIZE\[([0-9].*?)\]", r"^(\d+)$"]
        label_regex = r"[A-Za-z]+"
        # labels = [s.msgid for s in self.po_files]
        checks = [[".//viewtype[(@label)]", "label"],
                  [".//fontset[(@idloc)]", "idloc"],
                  [".//label[(@fallback)]", "fallback"]]
        for folder in self.addon.xml_folders:
            for xml_file in self.addon.window_files[folder]:
                path = os.path.join(self.addon.path, folder, xml_file)
                root = Utils.get_root_from_file(path)
                if root is None:
                    continue
                # find all referenced label ids (in element content)
                for element in root.xpath(".//label | .//altlabel | .//label2 | .//value | .//onclick | .//property"):
                    if not element.text:
                        continue
                    for match in re.finditer(regexs[0], element.text):
                        item = {"name": match.group(1),
                                "type": element.tag,
                                "file": path,
                                "line": element.sourceline}
                        refs.append(item)
                for element in root.xpath(".//label | .//altlabel | .//label2"):
                    if not element.text:
                        continue
                    if element.text.isdigit():
                        item = {"name": element.text,
                                "type": element.tag,
                                "file": path,
                                "line": element.sourceline}
                        refs.append(item)
                # check for untranslated strings...
                    elif "$" not in element.text and not len(element.text) == 1 and not element.text.endswith(".xml") and re.match(label_regex, element.text):
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
                        for regex in regexs:
                            for match in re.finditer(regex, attr):
                                item = {"name": match.group(1),
                                        "type": element.tag,
                                        "file": path,
                                        "line": element.sourceline}
                                refs.append(item)
                        # find some more untranslated strings
                        if "$" not in attr and not attr.isdigit() and re.match(label_regex, attr):
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
        listitems = []
        for path in self.addon.get_xml_files():
            new_items = self.check_file(path)
            listitems.extend(new_items)
        return listitems

    def check_file(self, path):
        xml_file = os.path.basename(path)
        # tags allowed for all controls
        root = Utils.get_root_from_file(path)
        if root is None:
            return []
        tree = ET.ElementTree(root)
        listitems = []
        # find invalid tags
        for check in TAG_CHECKS:
            for node in root.xpath(check[0]):
                if node.tag not in check[1]:
                    if "type" in node.getparent().attrib:
                        text = '%s type="%s"' % (node.getparent().tag, node.getparent().attrib["type"])
                    else:
                        text = node.getparent().tag
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "filename": xml_file,
                            "identifier": node.tag,
                            "message": "invalid tag for <%s>: <%s>" % (text, node.tag),
                            "file": path}
                    listitems.append(item)
        # find invalid attributes
        for check in ATT_CHECKS:
            xpath = ".//" + " | .//".join(check[0])
            for node in root.xpath(xpath):
                for attr in node.attrib:
                    if attr not in check[1]:
                        item = {"line": node.sourceline,
                                "type": node.tag,
                                "filename": xml_file,
                                "identifier": attr,
                                "message": "invalid attribute for <%s>: %s" % (node.tag, attr),
                                "file": path}
                        listitems.append(item)
        # check conditions in element content
        xpath = ".//" + " | .//".join(BRACKET_TAGS)
        for node in root.xpath(xpath):
            if not node.text:
                message = "Empty condition: %s" % (node.tag)
                condition = ""
            elif not Utils.check_brackets(node.text):
                condition = str(node.text).replace("  ", "").replace("\t", "")
                message = "Brackets do not match: %s" % (condition)
            else:
                continue
            item = {"line": node.sourceline,
                    "type": node.tag,
                    "filename": xml_file,
                    "identifier": condition,
                    "message": message,
                    "file": path}
            listitems.append(item)
        # check conditions in attribute values
        for node in root.xpath(".//*[@condition]"):
            if not Utils.check_brackets(node.attrib["condition"]):
                condition = str(node.attrib["condition"]).replace("  ", "").replace("\t", "")
                item = {"line": node.sourceline,
                        "type": node.tag,
                        "filename": xml_file,
                        "identifier": condition,
                        "message": "Brackets do not match: %s" % (condition),
                        "file": path}
                listitems.append(item)
        # check for noop as empty action
        xpath = ".//" + " | .//".join(NOOP_TAGS)
        for node in root.xpath(xpath):
            if node.text == "-" or not node.text:
                item = {"line": node.sourceline,
                        "type": node.tag,
                        "identifier": node.tag,
                        "filename": xml_file,
                        "message": "Use 'noop' for empty calls <%s>" % (node.tag),
                        "file": path}
                listitems.append(item)
        # check for not-allowed siblings for some tags
        xpath = ".//" + " | .//".join(DOUBLE_TAGS)
        for node in root.xpath(xpath):
            if not node.getchildren():
                xpath = tree.getpath(node)
                if xpath.endswith("]") and not xpath.endswith("[1]"):
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "filename": xml_file,
                            "identifier": node.tag,
                            "message": "Invalid multiple tags for %s: <%s>" % (node.getparent().tag, node.tag),
                            "file": path}
                    listitems.append(item)
        # Check tags which require specific values
        for check in ALLOWED_TEXT:
            xpath = ".//" + " | .//".join(check[0])
            for node in root.xpath(xpath):
                if node.text.startswith("$PARAM"):
                    continue
                if node.text.lower() not in check[1]:
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "identifier": node.text,
                            "filename": xml_file,
                            "message": "invalid value for %s: %s" % (node.tag, node.text),
                            "file": path}
                    listitems.append(item)
        # Check attributes which require specific values
        for check in ALLOWED_ATTR:
            for node in root.xpath(".//*[(@%s)]" % check[0]):
                if node.attrib[check[0]].startswith("$PARAM"):
                    continue
                if node.attrib[check[0]] not in check[1]:
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "identifier": node.attrib[check[0]],
                            "filename": xml_file,
                            "message": "invalid value for %s attribute: %s" % (check[0], node.attrib[check[0]]),
                            "file": path}
                    listitems.append(item)
        return listitems

    def check_file2(self, path):
        root = Utils.get_root_from_file(path)
        logging.info(path)
        if root is None:
            return []
        # tree = ET.ElementTree(root)
        listitems = []
        logging.info(self.template_root.tag)
        # find invalid tags
        all_controls = set([t.attrib.get("type") for t in self.template_root])
        xpath = " or ".join(["@type='{}'".format(c) for c in all_controls])
        xpath = ".//*[not({}) and @type[string()]]".format(xpath)
        logging.warning(xpath)
        for node in root.xpath(xpath):
            logging.warning(str(node.attrib))
        for template in self.template_root:
            tpl_tags = [child.tag for child in template.iterchildren()]
            logging.info(template.attrib.get("type"))
            for node in root.xpath(".//*[@type='%s']" % template.attrib.get("type")):
                for subnode in node.iterchildren():
                    if subnode.tag not in tpl_tags:
                        logging.info(subnode.tag)
                pass
        return listitems
