def test_get_current_timezone_templatetag_with_iana(self):
        tpl = Template(
            "{% load tz %}{% get_current_timezone as time_zone %}{{ time_zone }}"
        )
        tz = zoneinfo.ZoneInfo("Europe/Paris")
        with timezone.override(tz):
            self.assertEqual(tpl.render(Context()), "Europe/Paris")

        tpl = Template(
            "{% load tz %}{% timezone 'Europe/Paris' %}"
            "{% get_current_timezone as time_zone %}{% endtimezone %}"
            "{{ time_zone }}"
        )
        self.assertEqual(tpl.render(Context()), "Europe/Paris")