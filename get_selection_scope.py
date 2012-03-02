import sublime
import sublime_plugin


class GetSelectionScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()
        if len(sel) > 0:
            sublime.error_message(self.view.scope_name(sel[0].begin()))
