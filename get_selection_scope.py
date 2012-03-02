import sublime
import sublime_plugin


class GetSelectionScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()
        if len(sel) > 0 and sel[0].begin() == sel[0].end():
            sublime.error_message(self.view.scope_name(sel[0].begin()))
