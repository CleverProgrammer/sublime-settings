'''
Theme Tweaker
Licensed under MIT
Copyright (c) 2013 Isaac Muse <isaacmuse@gmail.com>
'''
import sublime
import sublime_plugin
from User.lib.rgba import RGBA
from os import makedirs
from os.path import join, basename, exists, abspath, dirname, normpath
from plistlib import readPlistFromBytes, writePlistToBytes
import re

PLUGIN_SETTINGS = "theme_tweaker.sublime-settings"
PREFERENCES = 'Preferences.sublime-settings'
TEMP_FOLDER = "ThemeTweaker"
TEMP_PATH = "Packages/User/%s" % TEMP_FOLDER
TWEAKED = TEMP_PATH + "/tweaked.tmTheme"
SCHEME = "color_scheme"
FILTER_MATCH = re.compile(r'^(?:(brightness|saturation|hue|colorize)\((-?[\d]+|[\d]*\.[\d]+)\)|(sepia|grayscale|invert))$')
IFILTER_MATCH = re.compile(r'^(?:(brightness|saturation|hue|colorize)\((-?[\d]+|-?[\d]*\.[\d]+)\)|(sepia|grayscale|invert))$')
TWEAK_MODE = False


class ToggleThemeTweakerModeCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        global TWEAK_MODE
        TWEAK_MODE = not TWEAK_MODE
        if not TWEAK_MODE:
            ThemeTweaker().clear_history()


class ThemeTweakerBrightnessCommand(sublime_plugin.ApplicationCommand):
    def run(self, direction="+"):
        magnitude = -1.0 if direction == "-" else 1.0
        value = float(sublime.load_settings(PLUGIN_SETTINGS).get("brightness_step", .01)) * magnitude
        if value > -1.0 and value < 1.0:
            ThemeTweaker().run("brightness(%f)" % (value + 1.0))


class ThemeTweakerSaturationCommand(sublime_plugin.ApplicationCommand):
    def run(self, direction="+"):
        magnitude = -1.0 if direction == "-" else 1.0
        value = float(sublime.load_settings(PLUGIN_SETTINGS).get("saturation_step", .1)) * magnitude
        if value > -1.0 and value < 1.0:
            ThemeTweaker().run("saturation(%f)" % (value + 1.0))


class ThemeTweakerHueCommand(sublime_plugin.ApplicationCommand):
    def run(self, direction="+"):
        magnitude = -1 if direction == "-" else 1
        value = int(sublime.load_settings(PLUGIN_SETTINGS).get("hue_step", 10)) * magnitude
        if value >= -360 and value <= 360:
            ThemeTweaker().run("hue(%d)" % value)


class ThemeTweakerInvertCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        ThemeTweaker().run("invert")


class ThemeTweakerSepiaCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        ThemeTweaker().run("sepia")


class ThemeTweakerGrayscaleCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        ThemeTweaker().run("grayscale")


class ThemeTweakerCustomCommand(sublime_plugin.ApplicationCommand):
    def run(self, filters):
        ThemeTweaker().run(filters)


class ThemeTweakerClearCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        ThemeTweaker().clear()


class ThemeTweakerUndoCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        ThemeTweaker().undo()


class ThemeTweakerRedoCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        ThemeTweaker().redo()


class ThemeTweaker(object):
    def _ensure_temp(self):
        temp = join(dirname(sublime.packages_path()), TEMP_PATH)
        if not exists(temp):
            makedirs(temp)

    def _theme_valid(self, scheme_file):
        is_working = scheme_file.startswith(TEMP_PATH + '/')
        if is_working and self.scheme_map is not None and self.scheme_map["working"] == scheme_file and exists(join(dirname(sublime.packages_path()), normpath(self.scheme_map["original"]))):
            self.scheme_file = join(dirname(sublime.packages_path()), normpath(self.scheme_map["original"]))
            self.scheme_clone = join(dirname(sublime.packages_path()), normpath(self.scheme_map["working"]))
            return True
        elif not is_working:
            self._ensure_temp()
            content = sublime.load_binary_resource(scheme_file)
            self.scheme_file = join(dirname(sublime.packages_path()), normpath(scheme_file))
            self.scheme_clone = join(dirname(sublime.packages_path()), normpath(TEMP_PATH), basename(scheme_file))
            try:
                with open(self.scheme_clone, "wb") as f:
                    f.write(content)
                self.scheme_map = {"original": scheme_file, "working": "%s/%s" % (TEMP_PATH, basename(scheme_file)), "undo": "", "redo": ""}
                self.settings.set(SCHEME, self.scheme_map["working"])
                self.p_settings.set("scheme_map", self.scheme_map)
                sublime.save_settings(PLUGIN_SETTINGS)
                return True
            except Exception as e:
                print(e)
                sublime.error_message("Cannot clone theme")
                return
        return False

    def _apply_filters(self, tmtheme, filters):
        def filter_color(color):
            rgba = RGBA(color)
            for f in self.filters:
                name = f[0]
                value = f[1]
                if name == "grayscale":
                    rgba.grayscale()
                elif name == "sepia":
                    rgba.sepia()
                elif name == "saturation":
                    rgba.saturation(value)
                elif name == "invert":
                    rgba.invert()
                elif name == "brightness":
                    rgba.brightness(value)
                elif name == "hue":
                    rgba.hue(value)
                elif name == "colorize":
                    rgba.colorize(value)
            return rgba.get_rgba()


        for f in filters.split(";"):
            m = FILTER_MATCH.match(f)
            if m:
                if m.group(1):
                    self.filters.append([m.group(1), float(m.group(2))])
                else:
                    self.filters.append([m.group(3), 0.0])

        if len(self.filters):
            general_settings_read = False
            for settings in tmtheme["settings"]:
                if not general_settings_read:
                    for k, v in settings["settings"].items():
                        try:
                            settings["settings"][k] = filter_color(v)
                        except:
                            pass
                    general_settings_read = True
                    continue

                try:
                    settings["settings"]["foreground"] = filter_color(settings["settings"]["foreground"])
                except:
                    pass
                try:
                    settings["settings"]["background"] = filter_color(settings["settings"]["background"])
                except:
                    pass
        return tmtheme

    def _get_filters(self):
        filters = []
        for f in self.filters:
            if f[0] in ["invert", "grayscale", "sepia"]:
                filters.append(f[0])
            if f[0] in ["hue", "colorize"]:
                filters.append(f[0] + "(%d)" % int(f[1]))
            if f[0] in ["saturation", "brightness"]:
                filters.append(f[0] + "(%f)" % f[1])
        return filters

    def clear(self):
        self.settings = sublime.load_settings(PREFERENCES)
        self.p_settings = sublime.load_settings(PLUGIN_SETTINGS)
        scheme_file = self.settings.get(SCHEME, None)
        self.scheme_map = self.p_settings.get("scheme_map", None)

        if self._theme_valid(scheme_file):
            with open(self.scheme_clone, "wb") as f:
                f.write(sublime.load_binary_resource(self.scheme_map["original"]))
                self.scheme_map["redo"] = ""
                self.scheme_map["undo"] = ""
                self.p_settings.set("scheme_map", self.scheme_map)
                sublime.save_settings(PLUGIN_SETTINGS)

    def clear_history(self):
        self.settings = sublime.load_settings(PREFERENCES)
        self.p_settings = sublime.load_settings(PLUGIN_SETTINGS)
        scheme_file = self.settings.get(SCHEME, None)
        self.scheme_map = self.p_settings.get("scheme_map", None)

        if self._theme_valid(scheme_file):
            self.scheme_map["redo"] = ""
            self.scheme_map["undo"] = ""
            self.p_settings.set("scheme_map", self.scheme_map)
            sublime.save_settings(PLUGIN_SETTINGS)

    def undo(self):
        self.filters = []
        self.settings = sublime.load_settings(PREFERENCES)
        self.p_settings = sublime.load_settings(PLUGIN_SETTINGS)
        scheme_file = self.settings.get(SCHEME, None)
        self.scheme_map = self.p_settings.get("scheme_map", None)

        if self._theme_valid(scheme_file):
            plist = sublime.load_binary_resource(self.scheme_map["original"])
            undo = self.scheme_map["undo"].split(";")
            if len(undo) == 0:
                return
            redo = self.scheme_map["redo"].split(";")
            redo.append(undo.pop())
            self.scheme_map["redo"] = ";".join(redo)
            self.scheme_map["undo"] = ";".join(undo)
            self.plist_file = self._apply_filters(
                readPlistFromBytes(plist),
                self.scheme_map["undo"]
            )
            with open(self.scheme_clone, "wb") as f:
                f.write(writePlistToBytes(self.plist_file))
                self.p_settings.set("scheme_map", self.scheme_map)
                sublime.save_settings(PLUGIN_SETTINGS)

    def redo(self):
        self.filters = []
        self.settings = sublime.load_settings(PREFERENCES)
        self.p_settings = sublime.load_settings(PLUGIN_SETTINGS)
        scheme_file = self.settings.get(SCHEME, None)
        self.scheme_map = self.p_settings.get("scheme_map", None)

        if self._theme_valid(scheme_file):
            plist = sublime.load_binary_resource(self.scheme_map["original"])
            redo = self.scheme_map["redo"].split(";")
            if len(redo) == 0:
                return
            undo = self.scheme_map["undo"].split(";")
            undo.append(redo.pop())
            self.scheme_map["redo"] = ";".join(redo)
            self.scheme_map["undo"] = ";".join(undo)
            self.plist_file = self._apply_filters(
                readPlistFromBytes(plist),
                self.scheme_map["undo"]
            )
            with open(self.scheme_clone, "wb") as f:
                f.write(writePlistToBytes(self.plist_file))
                self.p_settings.set("scheme_map", self.scheme_map)
                sublime.save_settings(PLUGIN_SETTINGS)

    def run(self, filters):
        self.filters = []
        self.settings = sublime.load_settings(PREFERENCES)
        self.p_settings = sublime.load_settings(PLUGIN_SETTINGS)
        scheme_file = self.settings.get(SCHEME, None)
        self.scheme_map = self.p_settings.get("scheme_map", None)

        if self._theme_valid(scheme_file):
            plist = sublime.load_binary_resource(self.scheme_map["working"])
            self.plist_file = self._apply_filters(
                readPlistFromBytes(plist),
                filters
            )

            with open(self.scheme_clone, "wb") as f:
                f.write(writePlistToBytes(self.plist_file))
                undo = self.scheme_map["undo"].split(";") + self._get_filters()
                self.scheme_map["redo"] = ""
                self.scheme_map["undo"] = ";".join(undo)
                self.p_settings.set("scheme_map", self.scheme_map)
                sublime.save_settings(PLUGIN_SETTINGS)


class ThemeTweakerListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        return key == "theme_tweaker" and TWEAK_MODE
