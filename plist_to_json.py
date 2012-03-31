import sublime
import sublime_plugin
import json
import StringIO
from plistlib import readPlist, writePlistToString


JSON_SYNTAX = "Packages/AAALanguages/Better Javascript/JSON.tmLanguage"
PLIST_SYNTAX = "Packages/XML/XML.tmLanguage"


class PlistToJsonCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        f = StringIO.StringIO(
            self.view.substr(
                sublime.Region(0, self.view.size())
            ).encode('utf8')
        )
        self.view.replace(
            edit,
            sublime.Region(0, self.view.size()),
            json.dumps(
                readPlist(f), indent=4, separators=(',', ': ')
            )
        )
        self.view.set_syntax_file(JSON_SYNTAX)


class JsonToPlistCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        j = json.loads(
            self.view.substr(
                sublime.Region(0, self.view.size())
            )
        )
        self.view.replace(
            edit,
            sublime.Region(0, self.view.size()),
            writePlistToString(j)
        )
        self.view.set_syntax_file(PLIST_SYNTAX)
