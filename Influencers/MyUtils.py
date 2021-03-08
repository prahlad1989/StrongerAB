sql_datetime_format = "%Y-%m-%d %H:%M:%S"
javascript_iso_format = ""
sql_date_format = "%Y-%m-%d"

from numbers import Number
def noneToZero(obj):
    if isinstance(obj, Number):
        return obj
    else:
        return 0
