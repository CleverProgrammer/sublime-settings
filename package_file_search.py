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


DEFAULT_FILES = [
    {"caption": "Settings Files",        "search": {"pattern": "*.sublime-settings", "deep_search": True}},
    {"caption": "Keymap Files",          "search": {"pattern": "*.sublime-keymap",   "deep_search": True}},
    {"caption": "Command Files",         "search": {"pattern": "*.sublime-commands", "deep_search": True}},
    {"caption": "Readme Files",          "search": {"pattern": "*readme*",           "deep_search": True}},
    {"caption": "Language Syntax Files", "search": {"pattern": "*tmLanguage",        "deep_search": True}},
    {"caption": "Snippet Files",         "search": {"pattern": "*.sublime-snippet",  "deep_search": True}},
    {"caption": "Preference Files",      "search": {"pattern": "*.tmPreferences",    "deep_search": True}},
    {"caption": "Color Scheme Files",    "search": {"pattern": "*.tmTheme",          "deep_search": True}},
    {"caption": "Theme Files",           "search": {"pattern": "*.sublime-theme",    "deep_search": True}},
    {"caption": "Python Source Files",   "search": {"pattern": "*.py",               "deep_search": True}}
]


class GetPackageFilesInputCommand(sublime_plugin.WindowCommand):
    def find_pattern(self, pattern, deep_search):
        if pattern != "":
            self.window.run_command("get_package_files", {"pattern": pattern, "deep_search": deep_search})

    def run(self, deep_search=True):
        self.window.show_input_panel(
            "File Pattern: ",
            "",
            lambda x: self.find_pattern(x, deep_search=deep_search),
            None,
            None
        )


class GetPackageFilesMenuCommand(sublime_plugin.WindowCommand):
    def find_files(self, value, patterns):
        if value > -1:
            pat = patterns[value]
            self.window.run_command("get_package_files", {"pattern": pat["pattern"], "deep_search": pat["deep_search"]})

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
    def find_files(self, files, pattern, settings, base=None):
        for f in files:
            if fnmatch(f, pattern):
                name = f if base == None else join(base, f)
                settings.append(name.replace(self.packages, "").lstrip("\\").lstrip("/"))

    def walk(self, settings, plugin, pattern, deep_search=True):
        if deep_search:
            for base, dirs, files in walk(plugin):
                self.find_files(files, pattern, settings, base)
        else:
            files = [join(plugin, item) for item in listdir(plugin) if not isdir(join(plugin, item))]
            self.find_files(files, pattern, settings)

    def open_file(self, value, settings):
        if value > -1:
            self.window.open_file(join(self.packages, settings[value]))

    def run(self, pattern, deep_search=True):
        self.packages = normpath(sublime.packages_path())
        settings = []
        plugins = [join(self.packages, item) for item in listdir(self.packages) if isdir(join(self.packages, item))]
        for plugin in plugins:
            self.walk(settings, plugin, pattern, deep_search)
        self.window.show_quick_panel(
            settings,
            lambda x: self.open_file(x, settings=settings)
        )
