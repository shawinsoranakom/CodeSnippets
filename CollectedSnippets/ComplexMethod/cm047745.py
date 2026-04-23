def format_date(
    env: Environment,
    value: datetime.datetime | datetime.date | str,
    lang_code: str | None = None,
    date_format: str | typing.Literal[False] = False,
) -> str:
    """
        Formats the date in a given format.

        :param env: an environment.
        :param date, datetime or string value: the date to format.
        :param string lang_code: the lang code, if not specified it is extracted from the
            environment context.
        :param string date_format: the format or the date (LDML format), if not specified the
            default format of the lang.
        :return: date formatted in the specified format.
        :rtype: string
    """
    if not value:
        return ''
    from odoo.fields import Datetime  # noqa: PLC0415
    if isinstance(value, str):
        if len(value) < DATE_LENGTH:
            return ''
        if len(value) > DATE_LENGTH:
            # a datetime, convert to correct timezone
            value = Datetime.from_string(value)
            value = Datetime.context_timestamp(env['res.lang'], value)
        else:
            value = Datetime.from_string(value)
    elif isinstance(value, datetime.datetime) and not value.tzinfo:
        # a datetime, convert to correct timezone
        value = Datetime.context_timestamp(env['res.lang'], value)

    lang = get_lang(env, lang_code)
    locale = babel_locale_parse(lang.code)
    if not date_format:
        date_format = posix_to_ldml(lang.date_format, locale=locale)

    assert isinstance(value, datetime.date)  # datetime is a subclass of date
    return babel.dates.format_date(value, format=date_format, locale=locale)