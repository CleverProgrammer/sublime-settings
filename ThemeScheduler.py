"""
Theme Scheduler

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
License: MIT

Example Theme file (ThemeScheduler.sublime-settings):
{
    "enabled": true,
    "themes":
    [
        {
            "theme": "Packages/User/Color Scheme/sometheme.tmTheme",
            "time": "21:30"
        },
        {
            "theme": "Packages/User/Color Scheme/someothertheme.tmTheme",
            "time": "8:30"
        }
    ]
}

Uses multiconf for "enabled" and "themes" key for platform or host specific settings.
See multiconf.py for more details.

Creates theme file if it doesn't exists (turned off by default).
"""

from datetime import datetime, timedelta
import time
import sublime
from collections import namedtuple
import thread
from ThemeSchedulerLib.file_strip.json import sanitize_json
from ThemeSchedulerLib.multiconf import get as multiget
import json
from os.path import exists, join, abspath, dirname


def create_settings(settings_path):
    err = False
    default_theme = {
        "enabled": False,
        "themes": [],
    }
    j = json.dumps(default_theme, sort_keys=True, indent=4, separators=(',', ': '))
    try:
        with open(settings_path, 'w') as f:
            f.write(j + "\n")
    except:
        err = True
    return err


def total_seconds(t):
    return (t.microseconds + (t.seconds + t.days * 24 * 3600) * 10 ** 6) / 10 ** 6


def get_current_time():
    now = datetime.now()
    seconds = total_seconds(timedelta(hours=now.hour, minutes=now.minute, seconds=now.second))
    return seconds, now


def translate_time(t):
    tm = time.strptime(t, '%H:%M')
    return total_seconds(timedelta(hours=tm.tm_hour, minutes=tm.tm_min, seconds=tm.tm_sec))


class ThemeRecord(namedtuple('ThemeRecord', ["time", "theme", "msg"])):
    pass


class ThreadMgr(object):
    restart = False
    kill = False


class ThemeScheduler(object):
    themes = []
    current_theme = ""
    next_change = None
    day = None
    ready = False
    busy = False

    @classmethod
    def init(cls):
        """
        Initialize theme changer object
        """
        cls.ready = False

        cls.themes = []
        for t in multiget(SETTINGS, "themes", []):
            theme_time = translate_time(t["time"])
            theme = t["theme"]
            msg = t.get("msg", None)
            cls.themes.append(ThemeRecord(theme_time, theme, msg))
        cls.get_next_change()
        cls.set_startup_theme()
        cls.ready = True

    @classmethod
    def set_startup_theme(cls):
        """
        Set startup theme
        """

        if cls.next_change is not None:
            closest = None
            greatest = None
            seconds = get_current_time()[0]
            for t in cls.themes:
                if t.time < seconds and (closest is None or t.time > closest.time):
                    closest = t
                elif greatest is None or t.time > greatest.time:
                    greatest = t
            if closest is None:
                closest = cls.next_change if greatest is None else greatest

            if closest is not None:
                cls.update_theme(closest.theme, closest.msg)

    @classmethod
    def get_next_change(cls):
        """
        Get the next time point in which the theme should change.  Store the theme record.
        """

        # Reset tracker members
        cls.next_change = None
        cls.day = None

        # Try and find the closest time point to switch the theme
        closest = None
        lowest = None
        seconds, now = get_current_time()
        for t in cls.themes:
            if seconds <= t.time and (closest is None or t.time < closest.time):
                closest = t
            elif lowest is None or t.time < lowest.time:
                lowest = t

        # Select the closest if there was one
        if closest is not None:
            cls.next_change = closest
        elif lowest is not None:
            cls.next_change = lowest
            cls.day = now.day

    @classmethod
    def change_theme(cls):
        """
        Change the theme and get the next time point to change themes.
        """

        # Change the theme
        if cls.next_change is not None and cls.next_change.theme != cls.current_theme:
            theme, msg = cls.next_change.theme, cls.next_change.msg
            # Get the next before changing
            cls.get_next_change()
            cls.update_theme(theme, msg)
            cls.current_theme = cls.next_change.theme
        else:
            # Get the next time point to change the theme
            cls.get_next_change()

    @classmethod
    def update_theme(cls, theme, msg):
        # When sublime is loading, the User preference file isn't available yet.
        # Sublime provides no real way to tell when things are intialized.
        # Handling the preference file ourselves allows us to avoid obliterating the User preference file.
        cls.busy = True
        pref_file = join(sublime.packages_path(), 'User', 'Preferences.sublime-settings')
        pref = {}
        if exists(pref_file):
            try:
                with open(pref_file, "r") as f:
                    # Allow C style comments and be forgiving of trailing commas
                    content = sanitize_json(f.read(), True)
                pref = json.loads(content)
            except:
                pass
        pref['color_scheme'] = theme
        j = json.dumps(pref, sort_keys=True, indent=4, separators=(',', ': '))
        try:
            with open(pref_file, 'w') as f:
                f.write(j + "\n")
            if msg is not None and isinstance(msg, basestring):
                sublime.message_dialog(msg)
        except:
            pass
        cls.busy = False


def theme_loop():
    """
    Loop for checking when to change the theme.
    """

    def is_update_time():
        update = False
        seconds, now = get_current_time()
        if not ThemeScheduler.busy and ThemeScheduler.next_change is not None:
            update = (
                (ThemeScheduler.day is None and seconds >= ThemeScheduler.next_change.time) or
                (ThemeScheduler.day != now.day and seconds >= ThemeScheduler.next_change.time)
            )
        return update

    sublime.set_timeout(ThemeScheduler.init, 0)

    while not ThreadMgr.restart and not ThreadMgr.kill:
        # Pop back into the main thread and check if time to change theme
        if ThemeScheduler.ready and is_update_time():
            sublime.set_timeout(ThemeScheduler.change_theme, 0)
        time.sleep(1)

    if ThreadMgr.restart:
        ThreadMgr.restart = False
        sublime.set_timeout(manage_thread, 0)
    if ThreadMgr.kill:
        ThreadMgr.kill = False


def manage_thread(first_time=False, restart=False):
    """
    Manage killing, starting, and restarting the thread
    """

    global running_theme_scheduler_loop
    if not multiget(SETTINGS, 'enabled', 'False'):
        running_theme_scheduler_loop = False
        ThreadMgr.kill
        print "Theme Scheduler: Kill Thread"
    elif not restart and (first_time or not running_theme_scheduler_loop):
        running_theme_scheduler_loop = True
        thread.start_new_thread(theme_loop, ())
        print "Theme Scheduler: Start Thread"
    else:
        running_theme_scheduler_loop = False
        ThreadMgr.restart = True
        print "Theme Scheduler: Restart Thread"

settings_file = __name__ + '.sublime-settings'
settings_path = join(dirname(abspath(__file__)), settings_file)
if not exists(settings_path):
    create_settings(settings_path)

# Init the settings object
SETTINGS = sublime.load_settings(settings_file)
SETTINGS.clear_on_change('reload')
SETTINGS.add_on_change('reload', manage_thread)

first_time = not 'running_theme_scheduler_loop' in globals()
running_theme_scheduler_loop = not first_time
manage_thread(first_time, not first_time)
