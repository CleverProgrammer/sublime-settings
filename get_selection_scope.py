import sublime
import sublime_plugin


class GetSelectionScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        scope = self.view.scope_name(self.view.sel()[0].b)
        if sublime.ok_cancel_dialog('Scope:\n' + scope + '\n\nCopy to clipboard?', 'Copy'):
            sublime.set_clipboard(scope)
