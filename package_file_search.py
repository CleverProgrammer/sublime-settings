'''
Package File Search
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
'''

import sublime
import sublime_plugin
from os.path import join, isdir, normpath, dirname, basename, splitext, exists
from os import listdir, walk
from fnmatch import fnmatch
import re
import zipfile
import tempfile


DEFAULT_FILES = [
    {"caption": "Settings Files",        "search": {"pattern": "*.sublime-settings", "regex": False}},
    {"caption": "Keymap Files",          "search": {"pattern": "*.sublime-keymap",   "regex": False}},
    {"caption": "Command Files",         "search": {"pattern": "*.sublime-commands", "regex": False}},
    {"caption": "Readme Files",          "search": {"pattern": "*readme*",           "regex": False}},
    {"caption": "Language Syntax Files", "search": {"pattern": "*tmLanguage",        "regex": False}},
    {"caption": "Snippet Files",         "search": {"pattern": "*.sublime-snippet",  "regex": False}},
    {"caption": "Preference Files",      "search": {"pattern": "*.tmPreferences",    "regex": False}},
    {"caption": "Color Scheme Files",    "search": {"pattern": "*.tmTheme",          "regex": False}},
    {"caption": "Theme Files",           "search": {"pattern": "*.sublime-theme",    "regex": False}},
    {"caption": "Python Source Files",   "search": {"pattern": "*.py",               "regex": False}}
]


def sublime_package_paths():
    return [sublime.installed_packages_path(), join(dirname(sublime.executable_path()), 'Packages')]


class GetPackageFilesInputCommand(sublime_plugin.WindowCommand):
    def find_pattern(self, pattern):
        regex = False
        # deep_search = True
        if pattern != "":
            # m = re.match(r"^\[deep_search=(true|false)\](.*)", pattern)
            # if m != None:
            #     deep_search = True if m.group(1) == "true" else False
            #     pattern = m.group(2)
            m = re.match(r"^[ \t]*`(.*)`[ \t]*$", pattern)
            if m != None:
                regex = True
                pattern = m.group(1)
            self.window.run_command(
                "get_package_files",
                {
                    "pattern": pattern,
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

    def walk(self, settings, plugin, pattern, regex=False):
        for base, dirs, files in walk(plugin):
            files = [join(base, f) for f in files]
            self.find_files(files, pattern, settings, regex)
        # else:
        #     files = [join(plugin, item) for item in listdir(plugin) if not isdir(join(plugin, item))]
        #     self.find_files(files, pattern, settings, regex)

    def open_file(self, value, settings):
        if value > -1:
            if value >= self.zipped_idx:
                self.open_zip_file(settings[value])
            else:
                self.window.open_file(join(self.packages, settings[value]))

    def open_zip_file(self, fn):
        file_name = None
        zip_package = None
        zip_file = None
        for zp in sublime_package_paths():
            items = fn.replace('\\', '/').split('/')
            zip_package = items.pop(0)
            zip_file = '/'.join(items)
            if exists(join(zp, zip_package)):
                zip_package = join(zp, zip_package)
                file_name = join(zp, fn)
                break

        if file_name is not None:
            with zipfile.ZipFile(zip_package, 'r') as z:
                text = z.read(z.getinfo(zip_file))
                t_dir = tempfile.mkdtemp(prefix='pkg_file_search_')
                with open(join(t_dir, basename(zip_file)), 'wb') as f:
                    f.write(text)
                view = self.window.open_file(f.name)
                view.set_read_only(True)

    def get_zip_packages(self, file_path):
        plugins = [join(file_path, item) for item in listdir(file_path) if fnmatch(item, "*.sublime-package")]
        return plugins

    def search_zipped_files(self):
        plugins = []
        for zp in sublime_package_paths():
            plugins += self.get_zip_packages(zp)
        return plugins

    def walk_zip(self, settings, plugin, pattern, regex):
        # psuedo_path = join(normpath(sublime.packages_path()), splitext(basename(plugin))[0])
        with zipfile.ZipFile(plugin, 'r') as z:
            zipped = [join(basename(plugin), normpath(fn)) for fn in sorted(z.namelist())]
            self.find_files(zipped, pattern, settings, regex)

    def run(self, pattern, regex=False):
        self.packages = normpath(sublime.packages_path())
        settings = []
        plugins = [join(self.packages, item) for item in listdir(self.packages) if isdir(join(self.packages, item))]
        for plugin in plugins:
            self.walk(settings, plugin, pattern.strip(), regex)

        self.zipped_idx = len(settings)

        zipped_plugins = self.search_zipped_files()
        for plugin in zipped_plugins:
            self.walk_zip(settings, plugin, pattern.strip(), regex)

        self.window.show_quick_panel(
            settings,
            lambda x: self.open_file(x, settings=settings)
        )
