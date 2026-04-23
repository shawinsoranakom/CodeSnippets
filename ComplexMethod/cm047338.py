def value_to_html(self, value, options):
        units = {unit: duration for unit, label, duration in TIMEDELTA_UNITS}

        locale = babel_locale_parse(self.user_lang().code)
        factor = units[options.get('unit', 'second')]
        round_to = units[options.get('round', 'second')]

        if options.get('digital') and round_to > 3600:
            round_to = 3600

        r = round((value * factor) / round_to) * round_to

        sections = []
        sign = ''
        if value < 0:
            r = -r
            sign = '-'

        if options.get('digital'):
            for _unit, _label, secs_per_unit in TIMEDELTA_UNITS:
                if secs_per_unit > 3600:
                    continue
                v, r = divmod(r, secs_per_unit)
                if not v and (secs_per_unit > factor or secs_per_unit < round_to):
                    continue
                sections.append(u"%02.0f" % int(round(v)))
            return sign + u':'.join(sections)

        for _unit, _label, secs_per_unit in TIMEDELTA_UNITS:
            v, r = divmod(r, secs_per_unit)
            if not v:
                continue
            try:
                section = babel.dates.format_timedelta(
                    v*secs_per_unit,
                    granularity=round_to,
                    add_direction=options.get('add_direction'),
                    format=options.get('format', 'long'),
                    threshold=1,
                    locale=locale)
            except KeyError:
                # in case of wrong implementation of babel, try to fallback on en_US locale.
                # https://github.com/python-babel/babel/pull/827/files
                # Some bugs already fixed in 2.10 but ubuntu22 is 2.8
                localeUS = babel_locale_parse('en_US')
                section = babel.dates.format_timedelta(
                    v*secs_per_unit,
                    granularity=round_to,
                    add_direction=options.get('add_direction'),
                    format=options.get('format', 'long'),
                    threshold=1,
                    locale=localeUS)
            if section:
                sections.append(section)

        if sign:
            sections.insert(0, sign)
        return u' '.join(sections)