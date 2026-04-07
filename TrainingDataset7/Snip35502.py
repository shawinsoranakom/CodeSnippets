def test_localtime_filters_do_not_raise_exceptions(self):
        """
        Test the |localtime, |utc, and |timezone filters on bad inputs.
        """
        tpl = Template(
            "{% load tz %}{{ dt }}|{{ dt|localtime }}|{{ dt|utc }}|{{ dt|timezone:tz }}"
        )
        with self.settings(USE_TZ=True):
            # bad datetime value
            ctx = Context({"dt": None, "tz": ICT})
            self.assertEqual(tpl.render(ctx), "None|||")
            ctx = Context({"dt": "not a date", "tz": ICT})
            self.assertEqual(tpl.render(ctx), "not a date|||")
            # bad timezone value
            tpl = Template("{% load tz %}{{ dt|timezone:tz }}")
            ctx = Context({"dt": datetime.datetime(2011, 9, 1, 13, 20, 30), "tz": None})
            self.assertEqual(tpl.render(ctx), "")
            ctx = Context(
                {"dt": datetime.datetime(2011, 9, 1, 13, 20, 30), "tz": "not a tz"}
            )
            self.assertEqual(tpl.render(ctx), "")