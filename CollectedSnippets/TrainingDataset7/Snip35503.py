def test_timezone_templatetag(self):
        """
        Test the {% timezone %} templatetag.
        """
        tpl = Template(
            "{% load tz %}"
            "{{ dt }}|"
            "{% timezone tz1 %}"
            "{{ dt }}|"
            "{% timezone tz2 %}"
            "{{ dt }}"
            "{% endtimezone %}"
            "{% endtimezone %}"
        )
        ctx = Context(
            {
                "dt": datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC),
                "tz1": ICT,
                "tz2": None,
            }
        )
        self.assertEqual(
            tpl.render(ctx),
            "2011-09-01T13:20:30+03:00|2011-09-01T17:20:30+07:00|"
            "2011-09-01T13:20:30+03:00",
        )