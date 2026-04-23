def match_and_return_openbb_keyword_date(keyword: str) -> str:  # noqa: PLR0911
    """Return OpenBB keyword into date.

    Parameters
    ----------
    keyword : str
        String with potential OpenBB keyword (e.g. 1MONTHAGO,LASTFRIDAY,3YEARSFROMNOW,NEXTTUESDAY)

    Returns
    ----------
        str: Date with format YYYY-MM-DD
    """
    now = datetime.now()
    for i, regex in enumerate([r"^\$(\d+)([A-Z]+)AGO$", r"^\$(\d+)([A-Z]+)FROMNOW$"]):
        match = re.match(regex, keyword)
        if match:
            integer_value = int(match.group(1))
            time_unit = match.group(2)
            clean_time = time_unit.upper()
            if "DAYS" in clean_time or "MONTHS" in clean_time or "YEARS" in clean_time:
                kwargs = {time_unit.lower(): integer_value}
                if i == 0:
                    return (now - relativedelta(**kwargs)).strftime("%Y-%m-%d")  # type: ignore
                return (now + relativedelta(**kwargs)).strftime("%Y-%m-%d")  # type: ignore

    match = re.search(r"\$LAST(\w+)", keyword)
    if match:
        time_unit = match.group(1)
        # Check if it corresponds to a month
        if time_unit in list(MONTHS_VALUE.keys()):
            the_year = now.year
            # Calculate the year and month for last month date
            if now.month <= MONTHS_VALUE[time_unit]:
                # If the current month is greater than the last date month, it means it is this year
                the_year = now.year - 1
            return datetime(the_year, MONTHS_VALUE[time_unit], 1).strftime("%Y-%m-%d")

        # Check if it corresponds to a week day
        if time_unit in list(WEEKDAY_VALUE.keys()):
            if datetime.weekday(now) > WEEKDAY_VALUE[time_unit]:
                return (
                    now
                    - timedelta(datetime.weekday(now))
                    + timedelta(WEEKDAY_VALUE[time_unit])
                ).strftime("%Y-%m-%d")
            return (
                now
                - timedelta(7)
                - timedelta(datetime.weekday(now))
                + timedelta(WEEKDAY_VALUE[time_unit])
            ).strftime("%Y-%m-%d")

    match = re.search(r"\$NEXT(\w+)", keyword)
    if match:
        time_unit = match.group(1)
        # Check if it corresponds to a month
        if time_unit in list(MONTHS_VALUE.keys()):
            # Calculate the year and month for next month date
            if now.month < MONTHS_VALUE[time_unit]:
                # If the current month is greater than the last date month, it means it is this year
                return datetime(now.year, MONTHS_VALUE[time_unit], 1).strftime(
                    "%Y-%m-%d"
                )

            return datetime(now.year + 1, MONTHS_VALUE[time_unit], 1).strftime(
                "%Y-%m-%d"
            )

        # Check if it corresponds to a week day
        if time_unit in list(WEEKDAY_VALUE.keys()):
            if datetime.weekday(now) < WEEKDAY_VALUE[time_unit]:
                return (
                    now
                    - timedelta(datetime.weekday(now))
                    + timedelta(WEEKDAY_VALUE[time_unit])
                ).strftime("%Y-%m-%d")
            return (
                now
                + timedelta(7)
                - timedelta(datetime.weekday(now))
                + timedelta(WEEKDAY_VALUE[time_unit])
            ).strftime("%Y-%m-%d")

    return ""