def test_naturaltime(self):
        class naive(datetime.tzinfo):
            def utcoffset(self, dt):
                return None

        test_list = [
            "test",
            now,
            now - datetime.timedelta(microseconds=1),
            now - datetime.timedelta(seconds=1),
            now - datetime.timedelta(seconds=30),
            now - datetime.timedelta(minutes=1, seconds=30),
            now - datetime.timedelta(minutes=2),
            now - datetime.timedelta(hours=1, minutes=30, seconds=30),
            now - datetime.timedelta(hours=23, minutes=50, seconds=50),
            now - datetime.timedelta(days=1),
            now - datetime.timedelta(days=500),
            now + datetime.timedelta(seconds=1),
            now + datetime.timedelta(seconds=30),
            now + datetime.timedelta(minutes=1, seconds=30),
            now + datetime.timedelta(minutes=2),
            now + datetime.timedelta(hours=1, minutes=30, seconds=30),
            now + datetime.timedelta(hours=23, minutes=50, seconds=50),
            now + datetime.timedelta(days=1),
            now + datetime.timedelta(days=2, hours=6),
            now + datetime.timedelta(days=500),
            now.replace(tzinfo=naive()),
            now.replace(tzinfo=datetime.UTC),
        ]
        result_list = [
            "test",
            "now",
            "now",
            "a second ago",
            "30\xa0seconds ago",
            "a minute ago",
            "2\xa0minutes ago",
            "an hour ago",
            "23\xa0hours ago",
            "1\xa0day ago",
            "1\xa0year, 4\xa0months ago",
            "a second from now",
            "30\xa0seconds from now",
            "a minute from now",
            "2\xa0minutes from now",
            "an hour from now",
            "23\xa0hours from now",
            "1\xa0day from now",
            "2\xa0days, 6\xa0hours from now",
            "1\xa0year, 4\xa0months from now",
            "now",
            "now",
        ]
        # Because of the DST change, 2 days and 6 hours after the chosen
        # date in naive arithmetic is only 2 days and 5 hours after in
        # aware arithmetic.
        result_list_with_tz_support = result_list[:]
        assert result_list_with_tz_support[-4] == "2\xa0days, 6\xa0hours from now"
        result_list_with_tz_support[-4] == "2\xa0days, 5\xa0hours from now"

        orig_humanize_datetime, humanize.datetime = humanize.datetime, MockDateTime
        try:
            with translation.override("en"):
                self.humanize_tester(test_list, result_list, "naturaltime")
                with override_settings(USE_TZ=True):
                    self.humanize_tester(
                        test_list, result_list_with_tz_support, "naturaltime"
                    )
        finally:
            humanize.datetime = orig_humanize_datetime