def format_datetime(
    env: Environment,
    value: datetime.datetime | str,
    tz: str | typing.Literal[False] = False,
    dt_format: str = 'medium',
    lang_code: str | None = None,
) -> str:
    """ Formats the datetime in a given format.

    :param env:
    :param str|datetime value: naive datetime to format either in string or in datetime
    :param str tz: name of the timezone  in which the given datetime should be localized
    :param str dt_format: “medium”, or “short” to use res.lang format with or without the
        seconds. Or a custom date/time pattern compatible with `babel` lib
    :param str lang_code: ISO code of the language to use to render the given datetime
    :rtype: str
    """
    if not value:
        return ''
    if isinstance(value, str):
        from odoo.fields import Datetime  # noqa: PLC0415
        timestamp = Datetime.from_string(value)
    else:
        timestamp = value

    tz_name = tz or env.user.tz or 'UTC'
    utc_datetime = pytz.utc.localize(timestamp, is_dst=False)
    try:
        context_tz = pytz.timezone(tz_name)
        localized_datetime = utc_datetime.astimezone(context_tz)
    except Exception:
        localized_datetime = utc_datetime

    lang = get_lang(env, lang_code)

    locale = babel_locale_parse(lang.code or lang_code)  # lang can be inactive, so `lang`is empty
    if not dt_format or dt_format == 'medium':
        date_format = posix_to_ldml(lang.date_format, locale=locale)
        time_format = posix_to_ldml(lang.time_format, locale=locale)
        dt_format = '%s %s' % (date_format, time_format)
    elif dt_format == 'short':
        date_format = posix_to_ldml(lang.date_format, locale=locale)
        time_format = posix_to_ldml(lang.time_format.replace(':%S', ''), locale=locale)
        dt_format = '%s %s' % (date_format, time_format)

    # Babel allows to format datetime in a specific language without change locale
    # So month 1 = January in English, and janvier in French
    # Formatting available here : http://babel.pocoo.org/en/latest/dates.html#date-fields
    return babel.dates.format_datetime(localized_datetime, dt_format, locale=locale)