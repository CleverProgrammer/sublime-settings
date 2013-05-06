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
FILTER_MATCH = re.compile(r'^(?:(brightness|saturation|hue|colorize|glow)\((-?[\d]+|[\d]*\.[\d]+)\)|(sepia|grayscale|invert))$')
TWEAK_MODE = False

def packages_path(pth):
    return join(dirname(sublime.packages_path()), normpath(pth))


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


class ThemeTweakerColorizeCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        value = int(sublime.load_settings(PLUGIN_SETTINGS).get("colorize_hue", 0))
        ThemeTweaker().run("colorize(%d)" % value)


class ThemeTweakerGlowCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        value = float(sublime.load_settings(PLUGIN_SETTINGS).get("glow_intensity", .2))
        ThemeTweaker().run("glow(%f)" % value)


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
        temp = packages_path(TEMP_PATH)
        if not exists(temp):
            makedirs(temp)

    def _exists(self, pth):
        found = False
        if exists(packages_path(pth)):
            found = True
        else:
            try:
                sublime.load_settings(pth)
                found = True
            except:
                pass
        return found

    def _theme_valid(self, scheme_file):
        is_working = scheme_file.startswith(TEMP_PATH + '/')
        if is_working and self.scheme_map is not None and self.scheme_map["working"] == scheme_file and self._exists(self.scheme_map["original"]):
            self.scheme_file = packages_path(self.scheme_map["original"])
            self.scheme_clone = packages_path(self.scheme_map["working"])
            return True
        elif not is_working:
            self._ensure_temp()
            content = sublime.load_binary_resource(scheme_file)
            self.scheme_file = packages_path(scheme_file)
            self.scheme_clone = packages_path(join(normpath(TEMP_PATH), basename(scheme_file)))
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

    def _apply_filter(self, color, f_name, value=None):
        if isinstance(color, RGBA):
            if value is None:
                color.__getattribute__(f_name)()
            else:
                color.__getattribute__(f_name)(value)

    def _filter_colors(self, bg=None, fg=None):
        try:
            assert(fg is not None)
            rgba_fg = RGBA(fg)
        except:
            rgba_fg = fg
        try:
            assert(bg is not None)
            rgba_bg = RGBA(bg)
        except:
            rgba_bg = bg
        for f in self.filters:
            name = f[0]
            value = f[1]
            if name in ["grayscale", "sepia", "invert"]:
                self._apply_filter(rgba_fg, name)
                self._apply_filter(rgba_bg, name)
            elif name in ["saturation", "brightness", "hue", "colorize"]:
                self._apply_filter(rgba_fg, name, value)
                self._apply_filter(rgba_bg, name, value)
            elif name == "glow" and isinstance(rgba_fg, RGBA) and (bg is None or bg.strip() == ""):
                rgba = RGBA(rgba_fg.get_rgba())
                rgba.apply_alpha(self.bground if self.bground != "" else "#FFFFFF")
                bg = rgba.get_rgb() + ("%02X" % int((255.0 * value)))
                try:
                    rgba_bg = RGBA(bg)
                except:
                    rgba_bg = bg
        return (rgba_bg.get_rgba() if isinstance(rgba_bg, RGBA) else rgba_bg, rgba_fg.get_rgba() if isinstance(rgba_fg, RGBA) else rgba_fg)

    def _apply_filters(self, tmtheme, filters):
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
                        v, _ = self._filter_colors(v)
                        settings["settings"][k] = v
                    general_settings_read = True
                    continue
                self.bground = RGBA(tmtheme["settings"][0]["settings"].get("background", '#FFFFFF')).get_rgb()
                self.fground = RGBA(tmtheme["settings"][0]["settings"].get("foreground", '#000000')).get_rgba()
                background, foreground = self._filter_colors(settings["settings"].get("background", None), settings["settings"].get("foreground", None))
                if foreground is not None:
                    settings["settings"]["foreground"] = foreground
                if background is not None:
                    settings["settings"]["background"] = background

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

    def _setup(self):
        self.filters = []
        self.settings = sublime.load_settings(PREFERENCES)
        self.p_settings = sublime.load_settings(PLUGIN_SETTINGS)
        scheme_file = self.settings.get(SCHEME, None)
        self.scheme_map = self.p_settings.get("scheme_map", None)
        self.theme_valid = self._theme_valid(scheme_file)

    def clear(self):
        self._setup()

        if self.theme_valid:
            with open(self.scheme_clone, "wb") as f:
                f.write(sublime.load_binary_resource(self.scheme_map["original"]))
                self.scheme_map["redo"] = ""
                self.scheme_map["undo"] = ""
                self.p_settings.set("scheme_map", self.scheme_map)
                sublime.save_settings(PLUGIN_SETTINGS)

    def clear_history(self):
        self._setup()

        if self.theme_valid:
            self.scheme_map["redo"] = ""
            self.scheme_map["undo"] = ""
            self.p_settings.set("scheme_map", self.scheme_map)
            sublime.save_settings(PLUGIN_SETTINGS)

    def undo(self):
        self._setup()

        if self.theme_valid:
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
        self._setup()

        if self.theme_valid:
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
        self._setup()

        if self.theme_valid:
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
