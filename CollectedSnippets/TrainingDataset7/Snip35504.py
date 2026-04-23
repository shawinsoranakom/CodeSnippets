def test_timezone_templatetag_with_iana(self):
        """
        Test the {% timezone %} templatetag with IANA time zone providers.
        """
        tpl = Template("{% load tz %}{% timezone tz %}{{ dt }}{% endtimezone %}")

        # Use a IANA timezone as argument
        tz = zoneinfo.ZoneInfo("Europe/Paris")
        ctx = Context(
            {
                "dt": datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT),
                "tz": tz,
            }
        )
        self.assertEqual(tpl.render(ctx), "2011-09-01T12:20:30+02:00")

        # Use a IANA timezone name as argument
        ctx = Context(
            {
                "dt": datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT),
                "tz": "Europe/Paris",
            }
        )
        self.assertEqual(tpl.render(ctx), "2011-09-01T12:20:30+02:00")