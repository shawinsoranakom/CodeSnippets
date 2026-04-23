def main(args=None):
    import argparse
    parser = argparse.ArgumentParser(color=True)
    textgroup = parser.add_argument_group('text only arguments')
    htmlgroup = parser.add_argument_group('html only arguments')
    textgroup.add_argument(
        "-w", "--width",
        type=int, default=2,
        help="width of date column (default 2)"
    )
    textgroup.add_argument(
        "-l", "--lines",
        type=int, default=1,
        help="number of lines for each week (default 1)"
    )
    textgroup.add_argument(
        "-s", "--spacing",
        type=int, default=6,
        help="spacing between months (default 6)"
    )
    textgroup.add_argument(
        "-m", "--months",
        type=int, default=3,
        help="months per row (default 3)"
    )
    htmlgroup.add_argument(
        "-c", "--css",
        default="calendar.css",
        help="CSS to use for page"
    )
    parser.add_argument(
        "-L", "--locale",
        default=None,
        help="locale to use for month and weekday names"
    )
    parser.add_argument(
        "-e", "--encoding",
        default=None,
        help="encoding to use for output (default utf-8)"
    )
    parser.add_argument(
        "-t", "--type",
        default="text",
        choices=("text", "html"),
        help="output type (text or html)"
    )
    parser.add_argument(
        "-f", "--first-weekday",
        type=int, default=0,
        help="weekday (0 is Monday, 6 is Sunday) to start each week (default 0)"
    )
    parser.add_argument(
        "year",
        nargs='?', type=int,
        help="year number"
    )
    parser.add_argument(
        "month",
        nargs='?', type=int,
        help="month number (1-12)"
    )

    options = parser.parse_args(args)

    if options.locale and not options.encoding:
        parser.error("if --locale is specified --encoding is required")
        sys.exit(1)

    locale = options.locale, options.encoding
    today = datetime.date.today()

    if options.type == "html":
        if options.locale:
            cal = LocaleHTMLCalendar(locale=locale)
        else:
            cal = HTMLCalendar()
        cal.setfirstweekday(options.first_weekday)
        encoding = options.encoding
        if encoding is None:
            encoding = 'utf-8'
        optdict = dict(encoding=encoding, css=options.css)
        write = sys.stdout.buffer.write

        if options.year is None:
            write(cal.formatyearpage(today.year, **optdict))
        else:
            if options.month:
                write(cal.formatmonthpage(options.year, options.month, **optdict))
            else:
                write(cal.formatyearpage(options.year, **optdict))
    else:
        if options.locale:
            cal = _CLIDemoLocaleCalendar(highlight_day=today, locale=locale)
        else:
            cal = _CLIDemoCalendar(highlight_day=today)
        cal.setfirstweekday(options.first_weekday)
        optdict = dict(w=options.width, l=options.lines)
        if options.month is None:
            optdict["c"] = options.spacing
            optdict["m"] = options.months
        else:
            _validate_month(options.month)
        if options.year is None:
            result = cal.formatyear(today.year, **optdict)
        elif options.month is None:
            result = cal.formatyear(options.year, **optdict)
        else:
            result = cal.formatmonth(options.year, options.month, **optdict)
        write = sys.stdout.write
        if options.encoding:
            result = result.encode(options.encoding)
            write = sys.stdout.buffer.write
        write(result)