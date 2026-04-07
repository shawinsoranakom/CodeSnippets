def _date_from_string(
    year, year_format, month="", month_format="", day="", day_format="", delim="__"
):
    """
    Get a datetime.date object given a format string and a year, month, and day
    (only year is mandatory). Raise a 404 for an invalid date.
    """
    format = year_format + delim + month_format + delim + day_format
    datestr = str(year) + delim + str(month) + delim + str(day)
    try:
        return datetime.datetime.strptime(datestr, format).date()
    except ValueError:
        raise Http404(
            _("Invalid date string “%(datestr)s” given format “%(format)s”")
            % {
                "datestr": datestr,
                "format": format,
            }
        )