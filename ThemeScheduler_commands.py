import sublime_plugin
import sublime


class TsSetAprosopoCommand(sublime_plugin.ApplicationCommand):
    def run(self, variant, color, dirty_color):
        sublime.run_command(
            "set_aprosopo_theme",
            {
                "theme": variant,
                "color": color
            }
        )
        sublime.run_command(
            "set_aprosopo_theme_dirty",
            {
                "theme": variant,
                "color": dirty_color
            }
        )
