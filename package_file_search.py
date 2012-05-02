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


DEFAULT_FILES = {
    "Settings":      ("*.sublime-settings", True),
    "Keymaps":       ("*.sublime-keymap", True),
    "Commands":      ("*.sublime-commands", True),
    "Readmes":       ("*readme*", True),
    "Languages":     ("*tmLanguage", True),
    "Snippets":      ("*.sublime-snippets", True),
    "Preferences":   ("*.tmPreferences", True),
    "Color Schemes": ("*.tmTheme", True),
    "Themes":        ("*.sublime-theme", True),
    "Python Source": ("*.py", True)
}


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
            self.window.run_command("get_package_files", {"pattern": pat[0], "deep_search": pat[1]})

    def run(self, pattern_list=DEFAULT_FILES):
        patterns = []
        types = []
        for k, v in pattern_list.items():
            patterns.append(v)
            types.append(k)
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
