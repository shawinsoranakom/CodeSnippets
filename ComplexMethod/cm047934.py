def _try_match_date_time(self, preview_values, options):
        # Or a date/datetime if it matches the pattern
        date_patterns = [options['date_format']] if options.get(
            'date_format') else []
        user_date_format = self.env['res.lang']._get_data(code=self.env.user.lang).date_format
        if user_date_format:
            try:
                to_re(user_date_format)
                date_patterns.append(user_date_format)
            except KeyError:
                pass
        date_patterns.extend(DATE_PATTERNS)
        match = check_patterns(date_patterns, preview_values)
        if match:
            options['date_format'] = match
            return ['date', 'datetime']

        datetime_patterns = [options['datetime_format']] if options.get(
            'datetime_format') else []
        datetime_patterns.extend(
            "%s %s" % (d, t)
            for d in date_patterns
            for t in TIME_PATTERNS
        )
        match = check_patterns(datetime_patterns, preview_values)
        if match:
            options['datetime_format'] = match
            return ['datetime']

        return []