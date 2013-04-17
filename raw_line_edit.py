"""
Raw Line Edit
Licensed under MIT
Copyright (c) 2011 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
import codecs
from os.path import basename
import re


def strip_carriage_returns(text):
    return re.sub(r"\r", "", text)


def add_carriage_returns(text):
    return re.sub(r"(?<!\r)\n", "\r\n", text)


class ToggleRawLineEditCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_name = self.view.file_name()
        if file_name is not None or self.view.settings().get("RawLineEdit", False):
            if self.view.settings().get("RawLineEdit", False):
                if self.view.is_dirty():
                    if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?"):
                        self.view.run_command("save")
                self.view.set_scratch(True)
                file_name = self.view.settings().get("RawLineEditFilename")
                win = self.view.window()
                temp = None
                if len(win.views()) <= 1:
                    temp = win.new_file()
                win.focus_view(self.view)
                win.run_command("close_file")
                new_view = win.open_file(file_name)
                if temp is not None:
                    win.focus_view(temp)
                    win.run_command("close_file")
                win.focus_view(new_view)
            else:
                if self.view.is_dirty():
                    if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?"):
                        sublime.view.run_command("save")
                with codecs.open(file_name, "r", "utf-8") as f:
                    self.view.replace(edit, sublime.Region(0, self.view.size()), f.read())
                    self.view.set_line_endings("Unix")
                    self.view.settings().set("RawLineEdit", True)
                    self.view.settings().set("RawLineEditFilename", file_name)
                    self.view.set_scratch(True)
                    self.view.set_read_only(True)


class RawLineInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit, style="Unix"):
        self.view.set_scratch(False)
        self.view.set_read_only(False)
        for s in reversed(self.view.sel()):
            line_region = self.view.full_line(s)
            if style == "Unix":
                self.view.replace(edit, line_region, strip_carriage_returns(self.view.substr(line_region)))
            else:
                self.view.replace(edit, line_region, add_carriage_returns(self.view.substr(line_region)))
        self.view.set_read_only(True)


class RawLineEditListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        handeled = False
        if view.settings().get("RawLineEdit", False) and key.startswith("raw_line_edit"):
            handeled = True
        return handeled
