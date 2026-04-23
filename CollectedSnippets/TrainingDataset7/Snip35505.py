def test_get_current_timezone_templatetag(self):
        """
        Test the {% get_current_timezone %} templatetag.
        """
        tpl = Template(
            "{% load tz %}{% get_current_timezone as time_zone %}{{ time_zone }}"
        )

        self.assertEqual(tpl.render(Context()), "Africa/Nairobi")
        with timezone.override(UTC):
            self.assertEqual(tpl.render(Context()), "UTC")

        tpl = Template(
            "{% load tz %}{% timezone tz %}{% get_current_timezone as time_zone %}"
            "{% endtimezone %}{{ time_zone }}"
        )

        self.assertEqual(tpl.render(Context({"tz": ICT})), "+0700")
        with timezone.override(UTC):
            self.assertEqual(tpl.render(Context({"tz": ICT})), "+0700")