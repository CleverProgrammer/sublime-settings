 # -*- coding: utf-8 -*-

"""
Calendar Viewer

Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""

from datetime import date
import sublime_plugin
import sublime
from User.CalendarLib.enum import enum
import re
from os.path import join


months = enum("January February March April May June July August September October November December", start=1, name="Months")
weekdays = enum("Monday Tuesday Wednesday Thursday Friday Saturday Sunday", start=1, name="Days")
cal_header = u"|{0:^69}|\n"
cal_row_top_div = u"-----------------------------------------------------------------------\n"
cal_row_mid_div = u"-----------------------------------------------------------------------\n"
cal_row_btm_div = u"-----------------------------------------------------------------------\n"
# cal_cell_center_highlight = u"...{0:.^3}..."
# cal_cell_outer_highlight = u"........."
cal_cell_center_highlight = u"   {0: ^3}   "
cal_cell_outer_highlight = u"         "
cal_cell_center_holiday = u"   {0: ^3}   "
cal_cell_outer_holiday = u"         "
cal_cell_center = u"   {0:^3}   "
cal_cell_outer = u"         "
cal_cell_empty = u"         "
cal_cell_empty_wall = u" "
cal_cell_wall = u"|"
cal_header_days = u"|   %s   |   %s   |   %s   |   %s   |   %s   |   %s   |   %s   |\n"

holidays = {}


class CalendarEventListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if view.settings().get("calendar_current", None) is not None and view.settings().get("calendar_today", None) is not None:
            if key == "calendar_view":
                return True
        return False


class Day(object):
    def __init__(self, day, month, year):
        self.day = int(day)
        self.month = month
        self.year = int(year)

    def __unicode__(self):
        return self.str

    def __str__(self):
        return (u"%d/%d/%d" % (self.month.value, self.day, self.year))


def get_today():
    obj = date.today()
    return Day(obj.day, months(obj.month), obj.year)


def is_holiday(month, day):
    return holidays.get(str(month), {}).get(day, None) is not None


def tx_day(day):
    m = re.match(r"^(\d+)[^\d](\d+)[^\d](\d+)$", day)
    if m:
        return Day(m.group(2), months(int(m.group(1))), m.group(3))
    else:
        return get_today()


def is_leap_year(year):
    return ((year % 4 == 0) and (year % 100 != 0)) or (year % 400 == 0)


def days_in_months(month, year):
    days = 31
    if month == months.February:
        days = 29 if is_leap_year(year) else 28
    elif month in [months.September, months.April, months.June, months.November]:
        days = 30
    return days


def show_calendar_row(first, last, today, month, empty_cells=(0, 0)):
    pos = enum("left center right")
    row = u""

    for p in pos:
        row += cal_cell_wall
        if empty_cells[0] > 0:
            row += (cal_cell_empty * empty_cells[0]) + (cal_cell_empty_wall * (empty_cells[0] - 1))
            row += cal_cell_wall
        for d in range(first, last):
            if d == today:
                if p == pos.center:
                    row += cal_cell_center_highlight.format(d)
                else:
                    row += cal_cell_outer_highlight
            elif is_holiday(month, d):
                if p == pos.center:
                    row += cal_cell_center_holiday.format(d)
                else:
                    row += cal_cell_outer_holiday
            else:
                if p == pos.center:
                    row += cal_cell_center.format(d)
                else:
                    row += cal_cell_outer
            row += cal_cell_wall
        if empty_cells[1] > 0:
            row += (cal_cell_empty * empty_cells[1]) + (cal_cell_empty_wall * (empty_cells[1] - 1))
            row += cal_cell_wall
        row += "\n"
    return row


def show_calendar_header(month, year, sunday_first):
    bfr = cal_row_top_div
    bfr += cal_header.format(u"%s %d" % (month, year))
    bfr += cal_row_mid_div
    if sunday_first:
        bfr += (cal_header_days % ((str(weekdays.Sunday)[0:3],) + tuple(str(weekdays[x])[0:3] for x in range(0, 6))))
    else:
        bfr += (cal_header_days % tuple(str(weekdays[x])[0:3] for x in range(0, 7)))
    return bfr


def show_calendar_month(year, month, day=0, sunday_first=True):
    num_days = days_in_months(month, year)
    weekday_month_start = weekdays(date(year, month, 1).isoweekday())
    if sunday_first:
        offset = int(weekday_month_start) if weekday_month_start != weekdays.Sunday else 0
    else:
        offset = int(weekday_month_start) - 1 if weekday_month_start != weekdays.Sunday else 6

    start_row = 0
    if (num_days + offset) % 7:
        end_row = (num_days + offset) / 7
        end_offset = (7 * (end_row + 1)) - (num_days + offset)
    else:
        end_row = ((num_days + offset) / 7) - 1
        end_offset = (7 * end_row) - (num_days + offset)

    bfr = show_calendar_header(month, year, sunday_first)
    for r in range(0, int(end_row) + 1):
        bfr += cal_row_mid_div
        if r == start_row and offset:
            start = 1
            end = 7 - offset + 1
            empty_cells = (offset, 0)
        elif r == end_row and end_offset:
            start = 1 + 7 - offset + (7 * (r - 1))
            end = num_days + 1
            empty_cells = (0, end_offset)
        else:
            start = 1 + 7 - offset + (7 * (r - 1))
            end = start + 7
            empty_cells = (0, 0)
        bfr += show_calendar_row(start, end, day, month, empty_cells)
    bfr += cal_row_btm_div
    return bfr


class CalendarLookupCommand(sublime_plugin.WindowCommand):
    def lookup(self, value):
        if value != "":
            m = re.match(r"^(\d+)[^\d](\d+)[^\d](\d+)$", value)
            if m:
                win = sublime.active_window()
                if win is not None:
                    win.run_command("calendar", {"day": value})

    def run(self):
        today = get_today()
        # Ask for date
        v = self.window.show_input_panel(
            "Date to Look Up: ",
            str(today),
            self.lookup,
            None,
            None
        )
        v.run_command("select_all")


class CalendarCommand(sublime_plugin.WindowCommand):
    def run(self, day=None):
        calendar_view_exists = False
        for v in self.window.views():
            if v.settings().get("calendar_today", None) is not None:
                view = v
                calendar_view_exists = True
                break

        if not calendar_view_exists:
            view = self.window.new_file()
            view.set_name(".calendar")
            view.settings().set("draw_white_space", "none")
        else:
            view.set_read_only(False)
            self.window.focus_view(view)

        view.run_command("show_calendar", {"day": day})


class ShowCalendarCommand(sublime_plugin.TextCommand):
    def run(self, edit, day):
        view = self.view
        today = get_today() if day is None else tx_day(day)
        bfr = show_calendar_month(today.year, today.month, today.day)
        view.set_syntax_file(join("Packages", "User", "Calendar.tmLanguage"))
        view.replace(edit, sublime.Region(0, view.size()), bfr)
        view.sel().clear()
        view.settings().set("calendar_current", {"month": str(today.month), "year": today.year})
        view.settings().set("calendar_today", {"month": str(today.month), "year": today.year, "day": today.day})
        view.set_scratch(True)
        view.set_read_only(True)


# class ImportIcalCommand(sublime_plugin.TextCommand):
#     entries = re.compile("BEGIN:VEVENT(.*)END:VEVENT", re.DOTALL | re.MULTILINE)

#     def get_entries(self, bfr):
#         entry = {}
#         found_entry = False
#         for line in bfr.split('\n'):
#             if not found_entry:
#                 if line == "BEGIN:VEVENT":
#                     found_entry = True
#                 continue
#             else:
#                 m = re.match(r"(?:(DTSTART)|(DTEND));VALUE=DATE:(.*)")
#                 if m is not None:
#                     entry["start" if m.group(1) else "end"] = m.group(3)
#                     continue

#                 m = re.match(r"SUMMARY")

#     def run(self, edit, append=False):
#         bfr = self.view.substr(sublime.Region(0, self.view.size()))
#         if not bfr.startswith("BEGIN:VCALENDAR"):
#             return

#         holidays.clear()
#         for entry in self.get_entries(bfr):
#             print "\nentry"
#             # print entry


class CalendarMonthNavCommand(sublime_plugin.TextCommand):
    def run(self, edit, reverse=False):
        current_month = self.view.settings().get("calendar_current", None)
        today = self.view.settings().get("calendar_today", None)
        if current_month is not None and today is not None:
            self.view.set_read_only(False)
            next = self.next(current_month, today) if not reverse else self.previous(current_month, today)
            self.view.replace(edit, sublime.Region(0, self.view.size()), show_calendar_month(next.year, next.month, next.day))
            self.view.sel().clear()
            self.view.settings().set("calendar_current", {"month": str(next.month), "year": next.year})
            self.view.set_read_only(True)

    def next(self, current, today):
        m = months(current["month"])
        next = months(int(m) + 1) if m != months.December else months.January
        year = current["year"] + 1 if next == months.January else current["year"]
        day = today["day"] if today["month"] == str(next) and year == today["year"] else 0
        return Day(day, next, year)

    def previous(self, current, today):
        m = months(current["month"])
        previous = months(int(m) - 1) if m != months.January else months.December
        year = current["year"] - 1 if previous == months.December else current["year"]
        day = today["day"] if today["month"] == str(previous) and year == today["year"] else 0
        return Day(day, previous, year)
