def strftest2(self, now):
        nowsecs = str(int(now))[:-1]
        now = self.now

        nonstandard_expectations = (
        # These are standard but don't have predictable output
            ('%c', fixasctime(time.asctime(now)), 'near-asctime() format'),
            ('%x', '%02d/%02d/%02d' % (now[1], now[2], (now[0]%100)),
            '%m/%d/%y %H:%M:%S'),
            ('%Z', '%s' % self.tz, 'time zone name'),

            # These are some platform specific extensions
            ('%D', '%02d/%02d/%02d' % (now[1], now[2], (now[0]%100)), 'mm/dd/yy'),
            ('%e', '%2d' % now[2], 'day of month as number, blank padded ( 0-31)'),
            ('%h', calendar.month_abbr[now[1]], 'abbreviated month name'),
            ('%k', '%2d' % now[3], 'hour, blank padded ( 0-23)'),
            ('%n', '\n', 'newline character'),
            ('%r', '%02d:%02d:%02d %s' % (self.clock12, now[4], now[5], self.ampm),
            '%I:%M:%S %p'),
            ('%R', '%02d:%02d' % (now[3], now[4]), '%H:%M'),
            ('%s', nowsecs, 'seconds since the Epoch in UCT'),
            ('%t', '\t', 'tab character'),
            ('%T', '%02d:%02d:%02d' % (now[3], now[4], now[5]), '%H:%M:%S'),
            ('%3y', '%03d' % (now[0]%100),
            'year without century rendered using fieldwidth'),
        )


        for e in nonstandard_expectations:
            try:
                result = time.strftime(e[0], now)
            except ValueError as result:
                msg = "Error for nonstandard '%s' format (%s): %s" % \
                      (e[0], e[2], str(result))
                if support.verbose:
                    print(msg)
                continue
            if re.match(escapestr(e[1], self.ampm), result):
                if support.verbose:
                    print("Supports nonstandard '%s' format (%s)" % (e[0], e[2]))
            elif not result or result[0] == '%':
                if support.verbose:
                    print("Does not appear to support '%s' format (%s)" % \
                           (e[0], e[2]))
            else:
                if support.verbose:
                    print("Conflict for nonstandard '%s' format (%s):" % \
                           (e[0], e[2]))
                    print("  Expected %s, but got %s" % (e[1], result))