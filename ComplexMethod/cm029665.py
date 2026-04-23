def __calc_date_time(self):
        # Set self.LC_date_time, self.LC_date, self.LC_time and
        # self.LC_time_ampm by using time.strftime().

        # Use (1999,3,17,22,44,55,2,76,0) for magic date because the amount of
        # overloaded numbers is minimized.  The order in which searches for
        # values within the format string is very important; it eliminates
        # possible ambiguity for what something represents.
        time_tuple = time.struct_time((1999,3,17,22,44,55,2,76,0))
        time_tuple2 = time.struct_time((1999,1,3,1,1,1,6,3,0))
        replacement_pairs = []

        # Non-ASCII digits
        if self.LC_alt_digits or self.LC_alt_digits is None:
            for n, d in [(19, '%OC'), (99, '%Oy'), (22, '%OH'),
                         (44, '%OM'), (55, '%OS'), (17, '%Od'),
                         (3, '%Om'), (2, '%Ow'), (10, '%OI')]:
                if self.LC_alt_digits is None:
                    s = chr(0x660 + n // 10) + chr(0x660 + n % 10)
                    replacement_pairs.append((s, d))
                    if n < 10:
                        replacement_pairs.append((s[1], d))
                elif len(self.LC_alt_digits) > n:
                    replacement_pairs.append((self.LC_alt_digits[n], d))
                else:
                    replacement_pairs.append((time.strftime(d, time_tuple), d))
        replacement_pairs += [
            ('1999', '%Y'), ('99', '%y'), ('22', '%H'),
            ('44', '%M'), ('55', '%S'), ('76', '%j'),
            ('17', '%d'), ('03', '%m'), ('3', '%m'),
            # '3' needed for when no leading zero.
            ('2', '%w'), ('10', '%I'),
        ]

        date_time = []
        for directive in ('%c', '%x', '%X', '%r'):
            current_format = time.strftime(directive, time_tuple).lower()
            current_format = current_format.replace('%', '%%')
            # The month and the day of the week formats are treated specially
            # because of a possible ambiguity in some locales where the full
            # and abbreviated names are equal or names of different types
            # are equal. See doc of __find_month_format for more details.
            lst, fmt = self.__find_weekday_format(directive)
            if lst:
                current_format = current_format.replace(lst[2], fmt, 1)
            lst, fmt = self.__find_month_format(directive)
            if lst:
                current_format = current_format.replace(lst[3], fmt, 1)
            if self.am_pm[1]:
                # Must deal with possible lack of locale info
                # manifesting itself as the empty string (e.g., Swedish's
                # lack of AM/PM info) or a platform returning a tuple of empty
                # strings (e.g., MacOS 9 having timezone as ('','')).
                current_format = current_format.replace(self.am_pm[1], '%p')
            for tz_values in self.timezone:
                for tz in tz_values:
                    if tz:
                        current_format = current_format.replace(tz, "%Z")
            # Transform all non-ASCII digits to digits in range U+0660 to U+0669.
            if not current_format.isascii() and self.LC_alt_digits is None:
                current_format = re_sub(r'\d(?<![0-9])',
                                        lambda m: chr(0x0660 + int(m[0])),
                                        current_format)
            for old, new in replacement_pairs:
                current_format = current_format.replace(old, new)
            # If %W is used, then Sunday, 2005-01-03 will fall on week 0 since
            # 2005-01-03 occurs before the first Monday of the year.  Otherwise
            # %U is used.
            if '00' in time.strftime(directive, time_tuple2):
                U_W = '%W'
            else:
                U_W = '%U'
            current_format = current_format.replace('11', U_W)
            date_time.append(current_format)
        self.LC_date_time = date_time[0]
        self.LC_date = date_time[1]
        self.LC_time = date_time[2]
        self.LC_time_ampm = date_time[3]