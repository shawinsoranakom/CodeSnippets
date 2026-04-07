def test_sanitize_strftime_format_with_escaped_percent(self):
        dt = datetime.date(1, 1, 1)
        for fmt, expected in [
            ("%%C", "%C"),
            ("%%F", "%F"),
            ("%%G", "%G"),
            ("%%Y", "%Y"),
            ("%%%%C", "%%C"),
            ("%%%%F", "%%F"),
            ("%%%%G", "%%G"),
            ("%%%%Y", "%%Y"),
        ]:
            with self.subTest(fmt=fmt):
                fmt = sanitize_strftime_format(fmt)
                self.assertEqual(dt.strftime(fmt), expected)

        for year in (1, 99, 999, 1000):
            dt = datetime.date(year, 1, 1)
            for fmt, expected in [
                ("%%%C", "%%%02d" % (year // 100)),
                ("%%%F", "%%%04d-01-01" % year),
                ("%%%G", "%%%04d" % year),
                ("%%%Y", "%%%04d" % year),
                ("%%%%%C", "%%%%%02d" % (year // 100)),
                ("%%%%%F", "%%%%%04d-01-01" % year),
                ("%%%%%G", "%%%%%04d" % year),
                ("%%%%%Y", "%%%%%04d" % year),
            ]:
                with self.subTest(year=year, fmt=fmt):
                    fmt = sanitize_strftime_format(fmt)
                    self.assertEqual(dt.strftime(fmt), expected)