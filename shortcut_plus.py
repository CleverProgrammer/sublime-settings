"""
Shortcut Plus

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
License: MIT

Example:  This shows how to define two shortcut profiles bound to shortcuts

    // Shortcut Plus Toggle
    {
        "keys": ["alt+`"],
        "command": "toggle_shortcut_plus",
        "context": [{"key": "toggle_shortcut_plus"}],
        "args": {"profile": "MyProfile1"}
    },
    // Shortcut Plus Toggle
    {
        "keys": ["ctrl+alt+`"],
        "command": "toggle_shortcut_plus",
        "context": [{"key": "toggle_shortcut_plus"}],
        "args": {"profile": "MyProfile2"}
    },

Example: This shows how to create shortcuts that execute only in a given shorcut profile
         The first is bound to Myprofile1 and shows a dialog when all selections are empty
         and the escape key is pressed.

         The other is bound to MyProfile2 and shows the inverse when escape is pressed.

         "shortcut_plus_test" is command only for testing.  You can use any command you want.

    // Shortcut Plus Test
    {
        "keys": ["escape"],
        "command": "shortcut_plus_test",
        "context":
        [
            {"key": "shortcut_plus:MyProfile1"},
            {"key": "selection_empty", "operator": "equal", "operand": true, "match_all": true}
        ],
        "args": {
            "msg": "All selection are empty!"
        }
    },
    // Shortcut Plus Test
    {
        "keys": ["escape"],
        "command": "shortcut_plus_test",
        "context":
        [
            {"key": "shortcut_plus:MyProfile2"},
            {"key": "selection_empty", "operator": "equal", "operand": false, "match_all": true}
        ],
        "args": {
            "msg": "All selections are not empty!"
        }
    }
"""

import sublime
import sublime_plugin


class ShortcutMode(object):
    enabled = False
    profile = ""


class ShortcutPlusModeListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        handeled = False
        if key == "toggle_shortcut_plus":
            handeled = True
        elif ShortcutMode.enabled and key.startswith("shortcut_plus:"):
            if ShortcutMode.profile == key[len("shortcut_plus:"):len(key)]:
                handeled = True
        return handeled


class ToggleShortcutPlusCommand(sublime_plugin.ApplicationCommand):
    def run(self, profile):
        if profile == "" or ShortcutMode.profile == profile:
            ShortcutMode.enabled = False
            ShortcutMode.profile = ""
        elif profile != ShortcutMode.profile:
            ShortcutMode.enabled = True
            ShortcutMode.profile = profile
        msg = "Shortcut Plus: %s" % (
            "%s Enabled" % ShortcutMode.profile if ShortcutMode.enabled else "Disabled"
        )
        sublime.status_message(msg)


class ShortcutPlusTestCommand(sublime_plugin.WindowCommand):
    def run(self, msg):
        sublime.message_dialog(msg)
