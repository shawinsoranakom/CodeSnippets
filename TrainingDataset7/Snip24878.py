def test_naturaltime_as_documented(self):
        """
        #23340 -- Verify the documented behavior of humanize.naturaltime.
        """
        time_format = "%d %b %Y %H:%M:%S"
        documented_now = datetime.datetime.strptime("17 Feb 2007 16:30:00", time_format)

        test_data = (
            ("17 Feb 2007 16:30:00", "now"),
            ("17 Feb 2007 16:29:31", "29 seconds ago"),
            ("17 Feb 2007 16:29:00", "a minute ago"),
            ("17 Feb 2007 16:25:35", "4 minutes ago"),
            ("17 Feb 2007 15:30:29", "59 minutes ago"),
            ("17 Feb 2007 15:30:01", "59 minutes ago"),
            ("17 Feb 2007 15:30:00", "an hour ago"),
            ("17 Feb 2007 13:31:29", "2 hours ago"),
            ("16 Feb 2007 13:31:29", "1 day, 2 hours ago"),
            ("16 Feb 2007 13:30:01", "1 day, 2 hours ago"),
            ("16 Feb 2007 13:30:00", "1 day, 3 hours ago"),
            ("17 Feb 2007 16:30:30", "30 seconds from now"),
            ("17 Feb 2007 16:30:29", "29 seconds from now"),
            ("17 Feb 2007 16:31:00", "a minute from now"),
            ("17 Feb 2007 16:34:35", "4 minutes from now"),
            ("17 Feb 2007 17:30:29", "an hour from now"),
            ("17 Feb 2007 18:31:29", "2 hours from now"),
            ("18 Feb 2007 16:31:29", "1 day from now"),
            ("26 Feb 2007 18:31:29", "1 week, 2 days from now"),
        )

        class DocumentedMockDateTime(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None or tz.utcoffset(documented_now) is None:
                    return documented_now
                else:
                    return documented_now.replace(tzinfo=tz) + tz.utcoffset(now)

        orig_humanize_datetime = humanize.datetime
        humanize.datetime = DocumentedMockDateTime
        try:
            for test_time_string, expected_natural_time in test_data:
                with self.subTest(test_time_string):
                    test_time = datetime.datetime.strptime(
                        test_time_string, time_format
                    )
                    natural_time = humanize.naturaltime(test_time).replace("\xa0", " ")
                    self.assertEqual(expected_natural_time, natural_time)
        finally:
            humanize.datetime = orig_humanize_datetime