def test_localtime_templatetag_and_filters(self):
        """
        Test the {% localtime %} templatetag and related filters.
        """
        datetimes = {
            "utc": datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC),
            "eat": datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT),
            "ict": datetime.datetime(2011, 9, 1, 17, 20, 30, tzinfo=ICT),
            "naive": datetime.datetime(2011, 9, 1, 13, 20, 30),
        }
        templates = {
            "notag": Template(
                "{% load tz %}"
                "{{ dt }}|{{ dt|localtime }}|{{ dt|utc }}|{{ dt|timezone:ICT }}"
            ),
            "noarg": Template(
                "{% load tz %}{% localtime %}{{ dt }}|{{ dt|localtime }}|"
                "{{ dt|utc }}|{{ dt|timezone:ICT }}{% endlocaltime %}"
            ),
            "on": Template(
                "{% load tz %}{% localtime on %}{{ dt }}|{{ dt|localtime }}|"
                "{{ dt|utc }}|{{ dt|timezone:ICT }}{% endlocaltime %}"
            ),
            "off": Template(
                "{% load tz %}{% localtime off %}{{ dt }}|{{ dt|localtime }}|"
                "{{ dt|utc }}|{{ dt|timezone:ICT }}{% endlocaltime %}"
            ),
        }

        # Transform a list of keys in 'datetimes' to the expected template
        # output. This makes the definition of 'results' more readable.
        def t(*result):
            return "|".join(datetimes[key].isoformat() for key in result)

        # Results for USE_TZ = True

        results = {
            "utc": {
                "notag": t("eat", "eat", "utc", "ict"),
                "noarg": t("eat", "eat", "utc", "ict"),
                "on": t("eat", "eat", "utc", "ict"),
                "off": t("utc", "eat", "utc", "ict"),
            },
            "eat": {
                "notag": t("eat", "eat", "utc", "ict"),
                "noarg": t("eat", "eat", "utc", "ict"),
                "on": t("eat", "eat", "utc", "ict"),
                "off": t("eat", "eat", "utc", "ict"),
            },
            "ict": {
                "notag": t("eat", "eat", "utc", "ict"),
                "noarg": t("eat", "eat", "utc", "ict"),
                "on": t("eat", "eat", "utc", "ict"),
                "off": t("ict", "eat", "utc", "ict"),
            },
            "naive": {
                "notag": t("naive", "eat", "utc", "ict"),
                "noarg": t("naive", "eat", "utc", "ict"),
                "on": t("naive", "eat", "utc", "ict"),
                "off": t("naive", "eat", "utc", "ict"),
            },
        }

        for k1, dt in datetimes.items():
            for k2, tpl in templates.items():
                ctx = Context({"dt": dt, "ICT": ICT})
                actual = tpl.render(ctx)
                expected = results[k1][k2]
                self.assertEqual(
                    actual, expected, "%s / %s: %r != %r" % (k1, k2, actual, expected)
                )

        # Changes for USE_TZ = False

        results["utc"]["notag"] = t("utc", "eat", "utc", "ict")
        results["ict"]["notag"] = t("ict", "eat", "utc", "ict")

        with self.settings(USE_TZ=False):
            for k1, dt in datetimes.items():
                for k2, tpl in templates.items():
                    ctx = Context({"dt": dt, "ICT": ICT})
                    actual = tpl.render(ctx)
                    expected = results[k1][k2]
                    self.assertEqual(
                        actual,
                        expected,
                        "%s / %s: %r != %r" % (k1, k2, actual, expected),
                    )