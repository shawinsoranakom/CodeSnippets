def test_naturalday_uses_localtime(self):
        # Regression for #18504
        # This is 2012-03-08HT19:30:00-06:00 in America/Chicago
        dt = datetime.datetime(2012, 3, 9, 1, 30, tzinfo=datetime.UTC)

        orig_humanize_datetime, humanize.datetime = humanize.datetime, MockDateTime
        try:
            with override_settings(TIME_ZONE="America/Chicago", USE_TZ=True):
                with translation.override("en"):
                    self.humanize_tester([dt], ["yesterday"], "naturalday")
        finally:
            humanize.datetime = orig_humanize_datetime