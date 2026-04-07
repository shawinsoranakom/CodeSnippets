def test_localtime_filters_with_iana(self):
        """
        Test the |localtime, |utc, and |timezone filters with iana zones.
        """
        # Use an IANA timezone as local time
        tpl = Template("{% load tz %}{{ dt|localtime }}|{{ dt|utc }}")
        ctx = Context({"dt": datetime.datetime(2011, 9, 1, 12, 20, 30)})

        with self.settings(TIME_ZONE="Europe/Paris"):
            self.assertEqual(
                tpl.render(ctx), "2011-09-01T12:20:30+02:00|2011-09-01T10:20:30+00:00"
            )

        # Use an IANA timezone as argument
        tz = zoneinfo.ZoneInfo("Europe/Paris")
        tpl = Template("{% load tz %}{{ dt|timezone:tz }}")
        ctx = Context(
            {
                "dt": datetime.datetime(2011, 9, 1, 13, 20, 30),
                "tz": tz,
            }
        )
        self.assertEqual(tpl.render(ctx), "2011-09-01T12:20:30+02:00")