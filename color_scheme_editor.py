import sublime
import sublime_plugin
from os.path import join, exists, basename, normpath, dirname
from os import makedirs
import subprocess

PLUGIN_NAME = "User"
THEME_EDITOR = None


class ColorSchemeEditorCommand(sublime_plugin.ApplicationCommand):
    def run(self, no_direct_edit=True):
        if THEME_EDITOR is None:
            return
        # Get current color scheme
        settings = sublime.load_settings('Preferences.sublime-settings')
        scheme_file = settings.get('color_scheme', None)

        # Get real path
        actual_scheme_file = join(dirname(sublime.packages_path()), normpath(scheme_file))
        if scheme_file is not None:
            # If scheme cannot be found, it is most likely in an archived package
            if (
                not exists(actual_scheme_file) or
                (no_direct_edit and not scheme_file.startswith("Packages/User/ColorSchemeEditorTemp"))
            ):
                # Create temp folder
                zipped_themes = join(sublime.packages_path(), "User", "ColorSchemeEditorTemp")
                if not exists(zipped_themes):
                    makedirs(zipped_themes)

                # Read theme file into memory and write out to the temp directory
                text = sublime.load_binary_resource(scheme_file)
                actual_scheme_file = join(zipped_themes, basename(scheme_file))
                try:
                    with open(actual_scheme_file, "wb") as f:
                        f.write(text)
                except:
                    sublime.error_message("Color Scheme Editor:\nCould not copy theme file to temp directory.")
                    return

                # Load unarchived theme
                scheme_file = settings.set('color_scheme', "Packages/User/ColorSchemeEditorTemp/%s" % basename(scheme_file))

            # Call the editor with the theme file
            subprocess.Popen([THEME_EDITOR, actual_scheme_file])


def plugin_loaded():
    global THEME_EDITOR
    platform = sublime.platform()

    # Pick the correct binary for the editor
    if platform == "osx":
        THEME_EDITOR = join(sublime.packages_path(), PLUGIN_NAME, "subclrschm.app", "Contents", "MacOS", "subclrschm")
    elif platform == "windows":
        THEME_EDITOR = join(sublime.packages_path(), PLUGIN_NAME, "subclrschm.exe")
    elif platform == "linux":
        sublime.error_message("Color Scheme Editor:\nSorry, currently no love for the penguin.\nLinux support coming in the future.")
