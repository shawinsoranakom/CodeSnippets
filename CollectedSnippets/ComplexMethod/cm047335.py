def value_to_html(self, value, options):
        if not value:
            return ''

        lang = self.user_lang()
        locale = babel_locale_parse(lang.code)
        if isinstance(value, str):
            value = fields.Datetime.from_string(value)

        if options.get('tz_name'):
            self = self.with_context(tz=options['tz_name'])
            tzinfo = babel.dates.get_timezone(options['tz_name'])
        else:
            tzinfo = None

        value = fields.Datetime.context_timestamp(self, value)

        if 'format' in options:
            pattern = options['format']
        else:
            if options.get('time_only'):
                strftime_pattern = lang.time_format
            elif options.get('date_only'):
                strftime_pattern = lang.date_format
            else:
                strftime_pattern = "%s %s" % (lang.date_format, lang.time_format)

            pattern = posix_to_ldml(strftime_pattern, locale=locale)

        if options.get('hide_seconds'):
            pattern = pattern.replace(":ss", "").replace(":s", "")

        if options.get('time_only'):
            return babel.dates.format_time(value, format=pattern, tzinfo=tzinfo, locale=locale)
        elif options.get('date_only'):
            return babel.dates.format_date(value, format=pattern, locale=locale)
        else:
            return babel.dates.format_datetime(value, format=pattern, tzinfo=tzinfo, locale=locale)