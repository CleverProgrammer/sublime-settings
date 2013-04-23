import sublime
import sublime_plugin
import time
from os import stat as osstat
from os import makedirs
from os.path import basename, join, exists
import difflib

MENU_FOLDER = "EasyDiff"
CONTEXT_MENU = "Context.sublime-menu"
LEFT = None
RIGHT = None
DIFF_MENU = '''[
    { "caption": "-" },
    {
        "caption": "EasyDiff",
        "children":
        [
            {
                "caption": "Set Left Buffer",
                "command": "easy_diff_set_left"
            },
            {
                "caption": "Compare View with \\"%(file_name)s\\"",
                "command": "easy_diff_compare_both"
            },
            { "caption": "-"},
            {
                "caption": "Set Clipboard to Left Buffer",
                "command": "easy_diff_set_left_clipboard"
            },
            {
                "caption": "Compare Clipboard with \\"%(file_name)s\\"",
                "command": "easy_diff_compare_both_clipboard"
            },
            { "caption": "-"},
            {
                "caption": "Set Selection(s) to Left Buffer",
                "command": "easy_diff_set_left_selection"
            },
            {
                "caption": "Compare Selection(s) with \\"%(file_name)s\\"",
                "command": "easy_diff_compare_both_selection"
            }
        ]
    },
    { "caption": "-"}
]
'''


def update_menu(name="..."):
    menu_path = join(sublime.packages_path(), "User", MENU_FOLDER)
    if not exists(menu_path):
        makedirs(menu_path)
    if exists(menu_path):
        menu = join(menu_path, CONTEXT_MENU)
        with open(menu, "w") as f:
            f.write(DIFF_MENU % {"file_name": name})


class EasyDiffView(object):
    def __init__(self, name, content):
        self.filename = name
        self.content = content
        self.time = time.ctime()

    def get_time(self):
        return self.time

    def file_name(self):
        return self.filename

    def substr(self, region):
        return self.content[region.begin():region.end() + 1]

    def size(self):
        return len(self.content)


class EasyDiffInput(object):
    def __init__(self, v1, v2):
        untitled = False
        self.f1 = v1.file_name()
        if self.f1 is None:
            self.f1 = "Untitled"
            untitled = True
            self.t1 = time.ctime()
        elif isinstance(v1, EasyDiffView):
            self.t1 = v1.get_time()
        else:
            self.t1 = time.ctime(osstat(self.f1).st_mtime)
        self.b1 = v1.substr(sublime.Region(0, v1.size())).splitlines()

        self.f2 = v2.file_name()
        if self.f2 is None:
            self.f2 = "Untitled2" if untitled else "Untitled"
            self.t2 = time.ctime()
        elif isinstance(v2, EasyDiffView):
            self.t2 = v2.get_time()
        else:
            self.t2 = time.ctime(osstat(self.f2).st_mtime)
        self.b2 = v2.substr(sublime.Region(0, v2.size())).splitlines()


class EasyDiff(object):
    @classmethod
    def compare(cls, inputs):
        diff = difflib.unified_diff(
            inputs.b1, inputs.b2,
            inputs.f1, inputs.f2,
            inputs.t1, inputs.t2,
            lineterm=''
        )
        result = u"\n".join(line for line in diff)

        if result == "":
            sublime.status_message("No Difference")
            return

        use_buffer = bool(sublime.load_settings("easy_diff.sublime-settings").get("use_buffer", False))

        win = sublime.active_window()
        if use_buffer:
            v = win.new_file()
            v.set_name("EasyDiff: %s -> %s (%s)" % (basename(inputs.f1), basename(inputs.f2), time.ctime()))
            v.set_scratch(True)
            v.assign_syntax('Packages/Diff/Diff.tmLanguage')
            v.run_command('append', {'characters': result})
        else:
            v = win.create_output_panel('easy_diff')
            v.assign_syntax('Packages/Diff/Diff.tmLanguage')
            v.run_command('append', {'characters': result})
            win.run_command("show_panel", {"panel": "output.easy_diff"})


class EasyDiffSetLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global LEFT
        LEFT = {"win_id": self.view.window().id(), "view_id": self.view.id(), "clip": None}
        name = self.view.file_name()
        if name is None:
            name = "Untitled"
        update_menu(basename(name))


class EasyDiffSetLeftClipboardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global LEFT
        LEFT = {"win_id": None, "view_id": None, "clip": EasyDiffView("**clipboard**", sublime.get_clipboard())}
        update_menu("**clipboard**")

    def is_enabled(self):
        return bool(sublime.load_settings("easy_diff.sublime-settings").get("use_clipboard", True))

    is_visible = is_enabled


class EasyDiffSelection(object):
    def get_selections(self):
        bfr = ""
        length = len(self.view.sel())
        for s in self.view.sel():
            if s.size() == 0:
                continue
            bfr += self.view.substr(s)
            if length > 1:
                bfr += "\n"
            length -= 1
        return bfr

    def has_selections(self):
        selections = False
        for s in self.view.sel():
            if s.size() > 0:
                selections = True
                break
        return selections


class EasyDiffSetLeftSelectionCommand(sublime_plugin.TextCommand, EasyDiffSelection):
    def run(self, edit):
        global LEFT
        LEFT = {"win_id": None, "view_id": None, "clip": EasyDiffView("**selection**", self.get_selections())}
        update_menu("**selection**")

    def is_enabled(self):
        return bool(sublime.load_settings("easy_diff.sublime-settings").get("use_selections", True)) and self.has_selections()

    is_visible = is_enabled


class EasyDiffCompareBothCommand(sublime_plugin.TextCommand):
    special = None

    def set_right(self):
        self.right = {"win_id": self.view.window().id(), "view_id": self.view.id(), "clip": None}

    def run(self, edit):
        self.set_right()

        lw = None
        rw = None
        lv = None
        rv = None

        for w in sublime.windows():
            if w.id() == LEFT["win_id"]:
                lw = w
            if w.id() == self.right["win_id"]:
                rw = w
            if lw is not None and rw is not None:
                break

        if lw is not None:
            for v in lw.views():
                if v.id() == LEFT["view_id"]:
                    lv = v
                    break
        else:
            if LEFT["clip"]:
                lv = LEFT["clip"]

        if rw is not None:
            for v in rw.views():
                if v.id() == self.right["view_id"]:
                    rv = v
                    break
        else:
            if self.right["clip"]:
                rv = self.right["clip"]

        if lv is not None and rv is not None:
            EasyDiff.compare(EasyDiffInput(lv, rv))
        else:
            print("Can't compare")


    def is_enabled(self):
        return LEFT is not None and self.is_visible()


class EasyDiffCompareBothClipboardCommand(EasyDiffCompareBothCommand):
    def set_right(self):
        self.right = {"win_id": None, "view_id": None, "clip": EasyDiffView("**clipboard**", sublime.get_clipboard())}

    def is_visible(self):
        return bool(sublime.load_settings("easy_diff.sublime-settings").get("use_clipboard", True))


class EasyDiffCompareBothSelectionCommand(EasyDiffCompareBothCommand, EasyDiffSelection):
    def set_right(self):
        self.right = {"win_id": None, "view_id": None, "clip": EasyDiffView("**selection**", self.get_selections())}

    def is_visible(self):
        return bool(sublime.load_settings("easy_diff.sublime-settings").get("use_selections", True)) and self.has_selections()


class EasyDiffListener(sublime_plugin.EventListener):
    def on_close(self, view):
        global LEFT
        vid = view.id()
        if LEFT is not None and vid == LEFT["view_id"]:
            LEFT = None
            update_menu()


def plugin_loaded():
    update_menu()
