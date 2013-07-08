import sublime_plugin
import sublime
import subprocess
from os.path import exists, abspath, normpath, isdir, dirname

NO_RUMMAGE = 0
NO_TARGET = 1

ERRS = {
    NO_RUMMAGE: "Nothing to rummage!",
    NO_TARGET: "Cannot find Rummage Binary!"
}


class RummageBase(object):
    def fail(self, code, alert=True):
        if alert:
            sublime.error_message(ERRS[code])
        else:
            print(ERRS[code])

    def get_rummage(self):
        binary = None
        for value in sublime.load_settings("rummage.sublime-settings").get("rummage_binary", []):
            platform = value.get("platform", None)
            if platform is not None and platform == sublime.platform():
                binary = value.get("binary", None)
                break
        if binary is not None and not exists(binary):
            binary = None
        return binary


class Rummage(RummageBase):
    def is_text_cmd(self):
        return isinstance(self, sublime_plugin.TextCommand)

    def is_win_cmd(self):
        return isinstance(self, sublime_plugin.WindowCommand)

    def get_target(self, paths=[]):
        target = None
        fail_code = NO_RUMMAGE
        if len(paths):
            target = paths[0]
        elif self.is_text_cmd():
            filename = self.view.file_name()
            if filename is not None and exists(filename):
                target = filename
            else:
                self.fail(fail_code)
        else:
            self.fail(fail_code)
        return target

    def rummage(self, paths=[]):
        target = self.get_target(paths)
        if target is None:
            return

        binary = self.get_rummage()

        if binary is not None:
            subprocess.Popen(
                [binary, "-s", target]
            )
        else:
            self.fail(NO_TARGET)


class RummageFileCommand(sublime_plugin.TextCommand, Rummage):
    def run(self, edit):
        self.rummage()


class RummageFolderCommand(sublime_plugin.WindowCommand, Rummage):
    def run(self, paths=[]):
        self.rummage(paths)


class RummageRegexTesterCommand(sublime_plugin.ApplicationCommand, RummageBase):
    def run(self):
        binary = self.get_rummage()

        if binary is not None:
            subprocess.Popen(
                [binary, "-r"]
            )
        else:
            self.fail(NO_TARGET)
