SHORT_MONTH = 30
LONG_MONTH = 31
FEB_MONTH = 28
FEB_LEAP_MONTH = 29

JAN = 1
FEB = 2
MAR = 3
APR = 4
MAY = 5
JUN = 6
JUL = 7
AUG = 8
SEP = 9
OCT = 10
NOV = 11
DEC = 12


# Test 1: 20140228
# Test 2: 20141231
# Test 3: 20140101


def is_leap_year(year):
    return ((year % 4 == 0) and (year % 100 != 0)) or (year % 400 == 0)


def days_in_months(month, year):
    days = LONG_MONTH
    if month == FEB:
        days = FEB_LEAP_MONTH if is_leap_year(year) else FEB_MONTH
    elif month in [SEP, APR, JUN, NOV]:
        days = SHORT_MONTH
    return days


def increment_by_day(day, month, year):
    mdays = days_in_months(month, year)
    if day == mdays:
        day = 1
        if month == DEC:
            month = JAN
            year += 1
        else:
            month += 1
    else:
        day += 1

    return day, month, year


def replace(m):
    g = m.groupdict()
    year = int(g["year"].lstrip("0"))
    month = int(g["month"].lstrip("0"))
    day = int(g["day"].lstrip("0"))

    day, month, year = increment_by_day(day, month, year)

    return "%04d%02d%02d" % (year, month, day)
