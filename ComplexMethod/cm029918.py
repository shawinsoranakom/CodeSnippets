def formatyear(self, theyear, w=2, l=1, c=6, m=3):
        """
        Returns a year's calendar as a multi-line string.
        """
        w = max(2, w)
        l = max(1, l)
        c = max(2, c)
        colwidth = (w + 1) * 7 - 1
        v = []
        a = v.append
        a(repr(theyear).center(colwidth*m+c*(m-1)).rstrip())
        a('\n'*l)
        header = self.formatweekheader(w)
        for (i, row) in enumerate(self.yeardays2calendar(theyear, m)):
            # months in this row
            months = range(m*i+1, min(m*(i+1)+1, 13))
            a('\n'*l)
            names = (self.formatmonthname(theyear, k, colwidth, False)
                     for k in months)
            a(formatstring(names, colwidth, c).rstrip())
            a('\n'*l)
            headers = (header for k in months)
            a(formatstring(headers, colwidth, c).rstrip())
            a('\n'*l)

            if (
                self.highlight_day
                and self.highlight_day.year == theyear
                and self.highlight_day.month in months
            ):
                month_pos = months.index(self.highlight_day.month)
            else:
                month_pos = None

            # max number of weeks for this row
            height = max(len(cal) for cal in row)
            for j in range(height):
                weeks = []
                for k, cal in enumerate(row):
                    if j >= len(cal):
                        weeks.append('')
                    else:
                        day = (
                            self.highlight_day.day if k == month_pos else None
                        )
                        weeks.append(
                            self.formatweek(cal[j], w, highlight_day=day)
                        )
                a(formatstring(weeks, colwidth, c).rstrip())
                a('\n' * l)
        return ''.join(v)