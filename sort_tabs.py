import sublime_plugin
import os
from operator import itemgetter


class SortTabsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_views = []
        win = self.view.window()
        curr_view = win.active_view()
        for vw in win.views():
            head, tail = os.path.split(vw.file_name())
            group, _ = win.get_view_index(vw)
            file_views.append((tail.lower(), vw, group))
        file_views.sort(key=itemgetter(2, 0))
        for index, (_, vw, group) in enumerate(file_views):
            if not index:
                prev_group = group
                moving_index = 0
            elif group > prev_group:
                    moving_index = 0
                    prev_group = group
            else:
                moving_index += 1
            win.set_view_index(vw, group, moving_index)
        win.focus_view(curr_view)
