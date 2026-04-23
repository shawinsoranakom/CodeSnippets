def format_time(
    env: Environment,
    value: datetime.time | datetime.datetime | str,
    tz: str | typing.Literal[False] = False,
    time_format: str = 'medium',
    lang_code: str | None = None,
) -> str:
    """ Format the given time (hour, minute and second) with the current user preference (language, format, ...)

        :param env:
        :param value: the time to format
        :type value: `datetime.time` instance. Could be timezoned to display tzinfo according to format
        :param tz: name of the timezone  in which the given datetime should be localized
        :param str time_format: “medium”, or “short” to use res.lang format with or without the
            seconds. Or a custom time pattern compatible with `babel` lib
        :param lang_code: ISO

        :rtype str
    """
    if not value:
        return ''

    if isinstance(value, datetime.time):
        localized_time = value
    else:
        if isinstance(value, str):
            from odoo.fields import Datetime  # noqa: PLC0415
            value = Datetime.from_string(value)
        assert isinstance(value, datetime.datetime)
        tz_name = tz or env.user.tz or 'UTC'
        utc_datetime = pytz.utc.localize(value, is_dst=False)
        try:
            context_tz = pytz.timezone(tz_name)
            localized_time = utc_datetime.astimezone(context_tz).timetz()
        except Exception:
            localized_time = utc_datetime.timetz()

    lang = get_lang(env, lang_code)
    locale = babel_locale_parse(lang.code)
    if not time_format or time_format == 'medium':
        time_format = posix_to_ldml(lang.time_format, locale=locale)
    elif time_format == 'short':
        time_format = posix_to_ldml(lang.time_format.replace(':%S', ''), locale=locale)

    return babel.dates.format_time(localized_time, format=time_format, locale=locale)