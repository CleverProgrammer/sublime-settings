import sublime_plugin
from datetime import datetime
import time


class InsertDateCommand(sublime_plugin.TextCommand):
    def run(self, edit, format="%Y-%m-%d"):
        date_time = datetime.now().strftime(format)
        for sel in self.view.sel():
            if sel.size() == 0:
                self.view.insert(edit, sel.begin(), date_time)

class InsertUtcDateCommand(sublime_plugin.TextCommand):
    def run(self, edit, format="%Y-%m-%d %H:%M:%S"):
        date_time = time.strftime(format, time.gmtime())
        for sel in self.view.sel():
            if sel.size() == 0:
                self.view.insert(edit, sel.begin(), date_time)
