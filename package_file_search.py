"""
Package File Search
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
"""

import sublime
import sublime_plugin
from os.path import join, isdir, normpath, dirname, basename, splitext, exists
from os import listdir, walk
from fnmatch import fnmatch
import re
import zipfile


# Syntax will only be used when extracting a file from an archive.
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


class WriteArchivedPackageContentCommand(sublime_plugin.TextCommand):
    bfr = None
    def run(self, edit):
        cls = WriteArchivedPackageContentCommand
        if cls.bfr is not None:
            self.view.set_read_only(False)
            self.view.set_scratch(True)
            self.view.replace(edit, sublime.Region(0, self.view.size()), cls.bfr)
            sels = self.view.sel()
            sels.clear()
            sels.add(0)
            cls.bfr = None
            self.view.set_read_only(True)


class GetPackageFilesInputCommand(sublime_plugin.WindowCommand):
    def find_pattern(self, pattern):
        regex = False
        if pattern != "":
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
                if re.match(pattern, f[0], re.IGNORECASE) != None:
                    settings.append([f[0].replace(self.packages, "").lstrip("\\").lstrip("/"), f[1]])
            else:
                if fnmatch(f[0], pattern):
                    settings.append([f[0].replace(self.packages, "").lstrip("\\").lstrip("/"), f[1]])

    def walk(self, settings, plugin, pattern, regex=False):
        for base, dirs, files in walk(plugin):
            files = [(join(base, f), "Packages") for f in files]
            self.find_files(files, pattern, settings, regex)

    def open_file(self, value, settings):
        if value > -1:
            if value >= self.zipped_idx:
                self.open_zip_file(settings[value][0])
            else:
                self.window.open_file(join(self.packages, settings[value][0]))

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
                view = self.window.open_file(file_name)
                WriteArchivedPackageContentCommand.bfr = text.decode('utf-8').replace('\r', '')
                sublime.set_timeout(lambda: view.run_command("write_archived_package_content"), 0)


    def get_zip_packages(self, file_path, package_type):
        plugins = [(join(file_path, item), package_type) for item in listdir(file_path) if fnmatch(item, "*.sublime-package")]
        return plugins

    def search_zipped_files(self):
        plugins = []
        st_packages = sublime_package_paths()
        plugins += self.get_zip_packages(st_packages[0], "Installed")
        plugins += self.get_zip_packages(st_packages[1], "Default")
        return plugins

    def walk_zip(self, settings, plugin, pattern, regex):
        # psuedo_path = join(normpath(sublime.packages_path()), splitext(basename(plugin))[0])
        with zipfile.ZipFile(plugin[0], 'r') as z:
            zipped = [(join(basename(plugin[0]), normpath(fn)), plugin[1]) for fn in sorted(z.namelist())]
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
