'''
Package File Search
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
'''

import sublime
import sublime_plugin
from os.path import join, isdir, normpath
from os import listdir, walk
from fnmatch import fnmatch
import re


DEFAULT_FILES = [
    {"caption": "Settings Files",        "search": {"pattern": "*.sublime-settings", "deep_search": True, "regex": False}},
    {"caption": "Keymap Files",          "search": {"pattern": "*.sublime-keymap",   "deep_search": True, "regex": False}},
    {"caption": "Command Files",         "search": {"pattern": "*.sublime-commands", "deep_search": True, "regex": False}},
    {"caption": "Readme Files",          "search": {"pattern": "*readme*",           "deep_search": True, "regex": False}},
    {"caption": "Language Syntax Files", "search": {"pattern": "*tmLanguage",        "deep_search": True, "regex": False}},
    {"caption": "Snippet Files",         "search": {"pattern": "*.sublime-snippet",  "deep_search": True, "regex": False}},
    {"caption": "Preference Files",      "search": {"pattern": "*.tmPreferences",    "deep_search": True, "regex": False}},
    {"caption": "Color Scheme Files",    "search": {"pattern": "*.tmTheme",          "deep_search": True, "regex": False}},
    {"caption": "Theme Files",           "search": {"pattern": "*.sublime-theme",    "deep_search": True, "regex": False}},
    {"caption": "Python Source Files",   "search": {"pattern": "*.py",               "deep_search": True, "regex": False}}
]


class GetPackageFilesInputCommand(sublime_plugin.WindowCommand):
    def find_pattern(self, pattern):
        regex = False
        deep_search = True
        if pattern != "":
            m = re.match(r"^\[deep_search=(true|false)\](.*)", pattern)
            if m != None:
                deep_search = True if m.group(1) == "true" else False
                pattern = m.group(2)
            m = re.match(r"^[ \t]*`(.*)`[ \t]*$", pattern)
            if m != None:
                regex = True
                pattern = m.group(1)
            self.window.run_command(
                "get_package_files",
                {
                    "pattern": pattern,
                    "deep_search": deep_search,
                    "regex": regex
                }
            )

    def run(self):
        self.window.show_input_panel(
            "File Pattern: ",
            "",
            self.find_pattern,
            None,
            None
        )


class GetPackageFilesMenuCommand(sublime_plugin.WindowCommand):
    def find_files(self, value, patterns):
        if value > -1:
            pat = patterns[value]
            sublime.set_timeout(
                lambda: self.window.run_command(
                    "get_package_files",
                    {
                        "pattern": pat["pattern"],
                        "deep_search": pat["deep_search"],
                        "regex": pat["regex"]
                    }
                ),
                100
            )

    def run(self, pattern_list=DEFAULT_FILES):
        patterns = []
        types = []
        for item in pattern_list:
            patterns.append(item["search"])
            types.append(item["caption"])
        self.window.show_quick_panel(
            types,
            lambda x: self.find_files(x, patterns=patterns)
        )


class GetPackageFilesCommand(sublime_plugin.WindowCommand):
    def find_files(self, files, pattern, settings, regex):
        for f in files:
            if regex:
                if re.match(pattern, f, re.IGNORECASE) != None:
                    settings.append(f.replace(self.packages, "").lstrip("\\").lstrip("/"))
            else:
                if fnmatch(f, pattern):
                    settings.append(f.replace(self.packages, "").lstrip("\\").lstrip("/"))

    def walk(self, settings, plugin, pattern, deep_search=True, regex=False):
        if deep_search:
            for base, dirs, files in walk(plugin):
                files = [join(base, f) for f in files]
                self.find_files(files, pattern, settings, regex)
        else:
            files = [join(plugin, item) for item in listdir(plugin) if not isdir(join(plugin, item))]
            self.find_files(files, pattern, settings, regex)

    def open_file(self, value, settings):
        if value > -1:
            self.window.open_file(join(self.packages, settings[value]))

    def run(self, pattern, deep_search=True, regex=False):
        self.packages = normpath(sublime.packages_path())
        settings = []
        plugins = [join(self.packages, item) for item in listdir(self.packages) if isdir(join(self.packages, item))]
        for plugin in plugins:
            self.walk(settings, plugin, pattern.strip(), deep_search, regex)
        self.window.show_quick_panel(
            settings,
            lambda x: self.open_file(x, settings=settings)
        )
